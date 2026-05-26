import 'dart:async';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class AlertService {
  final FlutterLocalNotificationsPlugin _notifications = FlutterLocalNotificationsPlugin();

  // Notification Setup
  Future<void> init() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidSettings);
    await _notifications.initialize(initSettings);

    final androidImplementation = _notifications.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    if (androidImplementation != null) {
      await androidImplementation.requestNotificationsPermission();
    }
  }

  // Notification Trigger
  void _triggerNotification(String body) async {
    const androidDetails = AndroidNotificationDetails(
      'reflect_os_alerts',
      'Mirror Alerts',
      importance: Importance.max,
      priority: Priority.high,
    );

    await _notifications.show(
      DateTime.now().millisecond,
      "ReflectStudio: Mood Update",
      body,
      const NotificationDetails(android: androidDetails),
    );
  }

  // S3 monitoring logic (Amplify v2 Syntax)
  void startMonitoring() {
    Timer.periodic(const Duration(seconds: 15), (timer) async {
      try {
        // 1. Find out who is logged into the app
        final attributes = await Amplify.Auth.fetchUserAttributes();
        final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
        final userId = emailAttr.value.replaceAll('@gmail.com', ''); // e.g., "john_doe"

        // 2. Only look for alerts inside THIS user's folder!
        final listResult = await Amplify.Storage.list(
          path: StoragePath.fromString('public/alerts/$userId/'),
        ).result; // .result is mandatory here

        // If there are new JSON files
        if (listResult.items.isNotEmpty) {
          for (var item in listResult.items) {
            // Verify it is an actual .json file and not just the directory path
            if (item.path.contains('.json')) {
              _triggerNotification("A negative mood was detected. Please check on your loved one.");

              // Remove the file from S3 to prevent showing the same alert repeatedly
              await Amplify.Storage.remove(
                path: StoragePath.fromString(item.path),
              ).result;
              
              print("✅ Alert processed and removed: ${item.path}");
            }
          }
        }
      } catch (e) {
        print("S3 Monitor Error: $e");
      }
    });
  }
}