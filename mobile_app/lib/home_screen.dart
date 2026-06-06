import 'dart:ui'; 
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart'; 
import 'package:flutter_animate/flutter_animate.dart';
import 'database_service.dart';
import 'slideshow_screen.dart';
import 'manage_family_members_screen.dart';
import 'manage_reminders_screen.dart'; 
import 'login_screen.dart'; 

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final DatabaseService _db = DatabaseService();
  final TextEditingController _speakController = TextEditingController();
  
  bool _isSendingMessage = false; 

  final Color _accentColor = const Color(0xFFC4D300); 
  final Color _bgDark = const Color(0xFF0A0B10);      
  final Color _glassWhite = Colors.white.withOpacity(0.05);
  final Color _glassBorder = Colors.white.withOpacity(0.1);

  // --- FIXED PUPPETEER LOGIC ---
  Future<void> _sendPuppeteerMessage() async {
    if (_speakController.text.trim().isEmpty) return;

    setState(() => _isSendingMessage = true);

    try {
      // Clean email to remove @gmail.com
      final attributes = await Amplify.Auth.fetchUserAttributes();
      final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
      final userPrefix = emailAttr.value.replaceAll('@gmail.com', '');

      final String timestamp = DateTime.now().millisecondsSinceEpoch.toString();
      
      // Send to notifications folder so it shows in the notification bar
      final String pathName = 'public/notifications/${userPrefix}_Alert_$timestamp.txt';

      await Amplify.Storage.uploadData(
        data: StorageDataPayload.string(_speakController.text.trim()),
        path: StoragePath.fromString(pathName),
      ).result;

      if (mounted) {
        _speakController.clear();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("✅ Alert Sent to Mirror!", style: GoogleFonts.outfit()),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
          )
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Failed to send: $e"), backgroundColor: Colors.red)
        );
      }
    } finally {
      if (mounted) setState(() => _isSendingMessage = false);
    }
  }

  Future<void> _logout() async {
    try {
      await Amplify.Auth.signOut();
      if (mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => const LoginScreen()));
      }
    } catch (e) {
      debugPrint("Error logging out: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true, 
      appBar: AppBar(
        title: Text("MAGIC MIRROR", 
          style: GoogleFonts.orbitron(color: Colors.white, fontSize: 24, letterSpacing: 2, fontWeight: FontWeight.bold)
        ).animate(onPlay: (controller) => controller.repeat(reverse: true))
         .shimmer(duration: 2.seconds, color: _accentColor.withOpacity(0.5)), // Shimmer effect for title
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(color: Colors.black.withOpacity(0.2)),
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white), 
            onPressed: _logout
          ).animate().fade(delay: 500.ms).scale()
        ],
      ),
      body: Stack(
        children: [
          // Animated Background Gradient 1
          Positioned(
            top: -100, left: -100,
            child: Container(
              width: 400, height: 400,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentColor.withOpacity(0.15), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.2, duration: 4.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds),
          ),
          // Animated Background Gradient 2
          Positioned(
            bottom: -50, right: -100,
            child: Container(
              width: 300, height: 300,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [Colors.cyan.withOpacity(0.1), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.3, duration: 5.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds, delay: 1.seconds),
          ),
          
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  StreamBuilder(
                    stream: _db.getSensorStream(),
                    builder: (context, snapshot) {
                      String temp = "--";
                      String humidity = "--";
                      if (snapshot.hasData) {
                        final data = snapshot.data as List<Map<String, dynamic>>;
                        for (var row in data) {
                          if (row['id'] == 'temp') temp = row['value'].toString();
                          if (row['id'] == 'humidity') humidity = row['value'].toString();
                        }
                      }
                      return Row(
                        children: [
                          _glassSensorCard(Icons.thermostat, "$temp°C", "Room Temp", Colors.orange),
                          const SizedBox(width: 16),
                          _glassSensorCard(Icons.water_drop, "$humidity%", "Humidity", Colors.blue),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 32),
                  _sectionTitle("QUICK ALERT"),
                  const SizedBox(height: 12),
                  _glassContainer(
                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 5),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _speakController,
                            style: GoogleFonts.outfit(color: Colors.white),
                            decoration: InputDecoration(
                              hintText: "Type temporary alert...",
                              hintStyle: GoogleFonts.outfit(color: Colors.white38),
                              border: InputBorder.none,
                              contentPadding: const EdgeInsets.symmetric(horizontal: 15),
                            ),
                          ),
                        ),
                        _isSendingMessage
                            ? const Padding(padding: EdgeInsets.all(12.0), child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFC4D300))))
                            : IconButton(
                                icon: Icon(Icons.send_rounded, color: _accentColor), 
                                onPressed: _sendPuppeteerMessage
                              ).animate(target: _speakController.text.isNotEmpty ? 1 : 0).scaleXY(end: 1.1).shimmer(),
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),
                  _sectionTitle("SYSTEM POWER"),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(child: _glassButton("REBOOT", Icons.restart_alt, Colors.cyan, () => _db.sendCommand('system', 'reboot'))),
                      const SizedBox(width: 16),
                      Expanded(child: _glassButton("SHUTDOWN", Icons.power_settings_new, Colors.redAccent, () => _db.sendCommand('system', 'shutdown'))),
                    ],
                  ),
                  const SizedBox(height: 20),
                  _fullWidthButton("MANAGE SLIDESHOW", Icons.photo_library, () => Navigator.push(context, MaterialPageRoute(builder: (context) => const SlideshowScreen()))),
                  const SizedBox(height: 20),
                  _fullWidthButton("FAMILY MEMBERS", Icons.group, () => Navigator.push(context, MaterialPageRoute(builder: (context) => const ManageFamilyMembersScreen()))),
                  const SizedBox(height: 20),
                  _fullWidthButton("SCHEDULED REMINDERS", Icons.event_note, () => Navigator.push(context, MaterialPageRoute(builder: (context) => const ManageRemindersScreen()))),
                  const SizedBox(height: 50),
                ].animate(interval: 100.ms).fade(duration: 500.ms).slideY(begin: 0.1, end: 0, curve: Curves.easeOutQuad),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // --- UI HELPERS ---
  Widget _fullWidthButton(String label, IconData icon, VoidCallback onTap) {
    return SizedBox(
      width: double.infinity, height: 55,
      child: ElevatedButton.icon(
        onPressed: onTap,
        icon: Icon(icon, color: Colors.black),
        label: Text(label, style: GoogleFonts.orbitron(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.black)),
        style: ElevatedButton.styleFrom(
          backgroundColor: _accentColor, 
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
          elevation: 5,
          shadowColor: _accentColor.withOpacity(0.5)
        ),
      ),
    ).animate(onPlay: (controller) => controller.repeat(reverse: true))
     .boxShadow(
       begin: BoxShadow(color: _accentColor.withOpacity(0.2), blurRadius: 5, spreadRadius: 0),
       end: BoxShadow(color: _accentColor.withOpacity(0.6), blurRadius: 15, spreadRadius: 2),
       duration: 2.seconds,
     );
  }

  Widget _sectionTitle(String text) => Text(text, style: GoogleFonts.orbitron(color: Colors.white54, fontSize: 12, letterSpacing: 2, fontWeight: FontWeight.bold));

  Widget _glassContainer({required Widget child, EdgeInsetsGeometry? padding}) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 10, spreadRadius: 2)
        ]
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            padding: padding ?? const EdgeInsets.all(20), 
            decoration: BoxDecoration(
              color: _glassWhite, 
              borderRadius: BorderRadius.circular(24), 
              border: Border.all(color: _glassBorder)
            ), 
            child: child
          ),
        ),
      ),
    );
  }

  Widget _glassButton(String label, IconData icon, Color color, VoidCallback onTap) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(24),
        splashColor: color.withOpacity(0.3),
        highlightColor: color.withOpacity(0.1),
        child: _glassContainer(
          padding: const EdgeInsets.symmetric(vertical: 20), 
          child: Column(
            children: [
              Icon(icon, color: color, size: 28)
                .animate(onPlay: (controller) => controller.repeat())
                .shimmer(duration: 2.seconds, delay: 1.seconds, color: Colors.white), 
              const SizedBox(height: 8), 
              Text(label, style: GoogleFonts.orbitron(color: color, fontSize: 12, fontWeight: FontWeight.bold))
            ]
          )
        )
      ),
    );
  }

  Widget _glassSensorCard(IconData icon, String value, String label, Color color) {
    return Expanded(
      child: _glassContainer(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, 
          children: [
            Container(
              padding: const EdgeInsets.all(10), 
              decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle), 
              child: Icon(icon, color: color, size: 24)
            ), 
            const SizedBox(height: 16), 
            Text(value, style: GoogleFonts.outfit(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w600)), 
            Text(label, style: GoogleFonts.outfit(color: Colors.white54, fontSize: 12, letterSpacing: 1))
          ]
        )
      )
    );
  }
}