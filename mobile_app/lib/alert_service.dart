import 'dart:async';
import 'dart:convert';
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
    print("📡 S3 Alert Monitor: Service started");
    Timer.periodic(const Duration(seconds: 15), (timer) async {
      try {
        // 1. Find out who is logged into the app
        final attributes = await Amplify.Auth.fetchUserAttributes();
        final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
        
        // Split on '@', trim, and force lowercase to match strictly case-sensitive S3 folder names
        final userId = emailAttr.value.split('@')[0].trim().toLowerCase();
        
        final targetPath = 'public/alerts/$userId/';
        print("🔍 S3 Alert Monitor: Checking path '$targetPath'...");

        // 2. Only look for alerts inside THIS user's folder!
        final listResult = await Amplify.Storage.list(
          path: StoragePath.fromString(targetPath),
        ).result; // .result is mandatory here

        print("📂 S3 Alert Monitor: Found ${listResult.items.length} items in folder");

        // If there are new JSON files
        if (listResult.items.isNotEmpty) {
          for (var item in listResult.items) {
            print("📄 S3 Alert Monitor: Processing file '${item.path}'");
            // Verify it is an actual .json file and not just the directory path
            if (item.path.contains('.json')) {
              String notificationMsg = "A negative mood was detected. Please check on your loved one.";
              try {
                final downloadResult = await Amplify.Storage.downloadData(
                  path: StoragePath.fromString(item.path),
                ).result;
                
                final String jsonString = utf8.decode(downloadResult.bytes);
                final Map<String, dynamic> data = jsonDecode(jsonString);
                
                final String memberName = data['user_id'] ?? 'family member';
                final String emotion = data['emotion'] ?? 'negative emotion';
                
                // Format emotion and name beautifully (e.g. SAD -> Sadness, ANGRY -> Anger)
                String displayEmotion = emotion;
                if (emotion.toUpperCase() == 'SAD') {
                  displayEmotion = 'Sadness';
                } else if (emotion.toUpperCase() == 'ANGRY') {
                  displayEmotion = 'Anger';
                } else {
                  displayEmotion = emotion.toLowerCase();
                  if (displayEmotion.isNotEmpty) {
                    displayEmotion = displayEmotion[0].toUpperCase() + displayEmotion.substring(1);
                  }
                }
                
                String displayName = memberName.toLowerCase();
                if (displayName.isNotEmpty) {
                  displayName = displayName[0].toUpperCase() + displayName.substring(1);
                }

                notificationMsg = "$displayEmotion detected on $displayName. Please check on them.";
              } catch (downloadErr) {
                print("⚠️ S3 Alert Monitor download/parse error: $downloadErr");
              }

              _triggerNotification(notificationMsg);

              // Remove the file from S3 to prevent showing the same alert repeatedly
              await Amplify.Storage.remove(
                path: StoragePath.fromString(item.path),
              ).result;
              
              print("✅ S3 Alert Monitor: Alert processed and removed: ${item.path}");
            }
          }
        }
      } catch (e, stacktrace) {
        print("❌ S3 Alert Monitor Error: $e");
        print(stacktrace);
      }
    });
  }
}