import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'login_screen.dart'; // <--- Critical Import
import 'home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  print("🔌 Connecting to Supabase...");

  // 👇 Initialize Supabase
  await Supabase.initialize(
    url: 'https://eyamhuymenvyxahfjgtv.supabase.co',
    anonKey: 'sb_publishable_xYQdpLn9eHl4oew339icug_GiUOfIQ7',
  );

  print("✅ Connected to Supabase!");

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'ReflectOS',
      
      // Use Dark Theme so your white text/icons show up correctly
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0A0B10), // Matches your background color
        primaryColor: const Color(0xFFC4D300), // Your Neon Gold
      ),
      
      // Start at the Login Screen
      home: const LoginScreen(),
    );
  }
}