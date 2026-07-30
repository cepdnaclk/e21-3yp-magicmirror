import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

class DatabaseService {
  late MqttServerClient _mqttClient;
  final StreamController<List<Map<String, dynamic>>> _sensorStreamCtrl = StreamController.broadcast();

  // 👇 REPLACE THIS WITH YOUR AWS IOT CORE ENDPOINT 👇
  static const String iotEndpoint = 'your-iot-endpoint.iot.us-east-1.amazonaws.com';

  DatabaseService() {
    _initMqtt();
  }

  // --- 1. AWS IOT CORE (MQTT) SETUP ---
  Future<void> _initMqtt() async {
    // Replace with your actual AWS IoT Core Endpoint
    final clientId = 'flutter_client_${DateTime.now().millisecondsSinceEpoch}';
    _mqttClient = MqttServerClient(iotEndpoint, clientId);
    _mqttClient.port = 8883;
    _mqttClient.secure = true;
    _mqttClient.logging(on: false);

    try {
      await _mqttClient.connect();
      print("✅ Connected to AWS IoT Core!");
      
      // Subscribe to mirror sensors
      _mqttClient.subscribe('reflectos/mirror/sensors', MqttQos.atLeastOnce);
      
      // Listen for incoming sensor data from Raspberry Pi
      _mqttClient.updates!.listen((List<MqttReceivedMessage<MqttMessage>> c) {
        final MqttPublishMessage recMess = c[0].payload as MqttPublishMessage;
        final String pt = MqttPublishPayload.bytesToStringAsString(recMess.payload.message);
        
        // Example Payload: {"temp": 24, "humidity": 60}
        final Map<String, dynamic> data = jsonDecode(pt);
        _sensorStreamCtrl.add([
          {'id': 'temp', 'value': data['temp']},
          {'id': 'humidity', 'value': data['humidity']},
        ]);
      });
    } catch (e) {
      print("❌ MQTT Connection failed: $e");
    }
  }

  // --- 2. LISTEN TO SENSORS ---
  Stream<List<Map<String, dynamic>>> getSensorStream() {
    return _sensorStreamCtrl.stream;
  }

  // --- 3. SEND COMMANDS TO IOT CORE ---
  Future<void> sendCommand(String id, String value) async {
    final builder = MqttClientPayloadBuilder();
    builder.addString(jsonEncode({'command': id, 'value': value}));
    
    _mqttClient.publishMessage(
      'reflectos/mirror/commands', 
      MqttQos.atLeastOnce, 
      builder.payload!
    );
  }

  // --- 4. UPLOAD PROFILE TO AWS S3 ---
  Future<void> uploadProfile({
    required String name, 
    required String role, 
    required String pin,
    required String theme,
    required Uint8List photoBytes,
  }) async {
    try {
      final fileName = '${name.toLowerCase().trim()}_${DateTime.now().millisecondsSinceEpoch}.jpg';
      final path = StoragePath.fromString('public/mirror_faces/$fileName');

      // Upload Bytes to S3
      await Amplify.Storage.uploadData(
        data: StorageDataPayload.bytes(photoBytes),
        path: path,
      ).result;

      // Get Public URL
      final getUrlResult = await Amplify.Storage.getUrl(path: path).result;

      // Note: You would save the User Profile to AWS DynamoDB here via Amplify.API.mutate()
      // e.g., await Amplify.API.mutate(request: GraphQLRequest(...));
      
      print("Profile uploaded! Photo URL: ${getUrlResult.url}");
    } catch (e) {
      throw "Upload Error: $e";
    }
  }
}