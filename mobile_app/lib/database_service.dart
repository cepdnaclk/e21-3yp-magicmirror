import 'dart:typed_data'; // <--- NEW: For Web Support
import 'package:supabase_flutter/supabase_flutter.dart';

class DatabaseService {
  final _supabase = Supabase.instance.client;

  // 1. LISTEN TO SENSORS
  Stream<List<Map<String, dynamic>>> getSensorStream() {
    return _supabase.from('sensors').stream(primaryKey: ['id']).order('id');
  }

  // 2. SEND COMMANDS
  Future<void> sendCommand(String id, String value) async {
    await _supabase.from('commands').upsert({
      'id': id,
      'value': value,
      'updated_at': DateTime.now().toIso8601String(),
    });
  }

  // 3. UPLOAD PROFILE (WEB COMPATIBLE)
  Future<void> uploadProfile({
    required String name, 
    required String role, 
    required String pin,
    required String theme,
    required Uint8List photoBytes, // <--- CHANGED: Now accepts Bytes, not File
  }) async {
    final fileName = '${name.toLowerCase().trim()}.jpg';
    
    try {
      // Upload Raw Bytes (Works on Web & Mobile)
      await _supabase.storage.from('mirror_faces').uploadBinary(
        fileName,
        photoBytes,
        fileOptions: const FileOptions(upsert: true),
      );

      final publicUrl = _supabase.storage.from('mirror_faces').getPublicUrl(fileName);

      // Save Data
      await _supabase.from('users').upsert({
        'name': name,
        'role': role,
        'pin_code': pin,
        'theme': theme,
        'photo_url': publicUrl,
      });
    } catch (e) {
      throw "Upload Error: $e";
    }
  }
}