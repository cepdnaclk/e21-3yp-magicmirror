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

  // Notification Trigger (English)
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
        // v2 Syntax: StoragePath.fromString භාවිතා කළ යුතුයි
        final listResult = await Amplify.Storage.list(
          path: const StoragePath.fromString('public/alerts/'),
        ).result; // මෙහි .result අනිවාර්යයි

        // අලුත් JSON files තිබේ නම්
        if (listResult.items.isNotEmpty) {
          for (var item in listResult.items) {
            // "alerts/" කියන path එක පමණක් නොව ඇත්තම file එකක් දැයි බැලීම
            if (item.path.contains('.json')) {
              _triggerNotification("A negative mood was detected. Please check on your loved one.");

              // එකම alert එක නැවත පෙන්වීම වැළැක්වීමට S3 එකෙන් file එක අයින් කිරීම
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