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
  String _userEmail = '';

  final Color _accentCyan = const Color(0xFF00F0FF);
  final Color _accentPurple = const Color(0xFF9E00FF);
  final Color _accentPink = const Color(0xFFFF007A); 

  final List<Map<String, String>> _alertTemplates = [
    {"icon": "🍽️", "label": "Lunch is ready!"},
    {"icon": "💊", "label": "Time for medicine"},
    {"icon": "⏰", "label": "Time to wake up!"},
    {"icon": "🚗", "label": "I'm coming home"},
    {"icon": "🚪", "label": "Check the door"},
  ];

  Future<void> _sendDirectAlert(String message) async {
    setState(() => _isSendingMessage = true);

    try {
      final attributes = await Amplify.Auth.fetchUserAttributes();
      final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
      final userPrefix = emailAttr.value.replaceAll('@gmail.com', '');

      final String timestamp = DateTime.now().millisecondsSinceEpoch.toString();
      final String pathName = 'public/notifications/${userPrefix}_Alert_$timestamp.txt';

      await Amplify.Storage.uploadData(
        data: StorageDataPayload.string(message),
        path: StoragePath.fromString(pathName),
      ).result;

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("✅ Alert Sent: \"$message\"", style: GoogleFonts.outfit()),
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
  final Color _bgDark = const Color(0xFF07080E);      
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

  @override
  void initState() {
    super.initState();
    _fetchUserInfo();
  }

  Future<void> _fetchUserInfo() async {
    try {
      final attributes = await Amplify.Auth.fetchUserAttributes();
      final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
      setState(() {
        _userEmail = emailAttr.value.split('@')[0];
      });
    } catch (e) {
      debugPrint("Error fetching user info: $e");
    }
  }

  Future<void> _sendPuppeteerMessage() async {
    if (_speakController.text.trim().isEmpty) return;

    setState(() => _isSendingMessage = true);

    try {
      final attributes = await Amplify.Auth.fetchUserAttributes();
      final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
      final userPrefix = emailAttr.value.replaceAll('@gmail.com', '');

      final String timestamp = DateTime.now().millisecondsSinceEpoch.toString();
      final String pathName = 'public/notifications/${userPrefix}_Alert_$timestamp.txt';

      await Amplify.Storage.uploadData(
        data: StorageDataPayload.string(_speakController.text.trim()),
        path: StoragePath.fromString(pathName),
      ).result;

      if (mounted) {
        _speakController.clear();
        setState(() {}); // refresh send button status
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

  Future<void> _confirmSystemCommand(String command, String title) async {
    bool confirm = await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: _bgDark,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide(color: _glassBorder),
        ),
        title: Text(
          "$title Mirror?",
          style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
        ),
        content: Text(
          "Are you sure you want to request a system $command for the smart mirror?",
          style: GoogleFonts.outfit(color: Colors.white54, fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text("CANCEL", style: GoogleFonts.outfit(color: Colors.white54)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(
              title.toUpperCase(),
              style: GoogleFonts.outfit(
                color: command == 'shutdown' ? Colors.redAccent : Colors.cyan,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    ) ?? false;

    if (confirm) {
      await _db.sendCommand('system', command);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("📡 Sent $title command to mirror...", style: GoogleFonts.outfit()),
            backgroundColor: Colors.indigoAccent,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true, 
      appBar: AppBar(
        title: Text("REFLECTSTUDIO", 
          style: GoogleFonts.orbitron(color: Colors.white, fontSize: 20, letterSpacing: 3, fontWeight: FontWeight.bold)
        ).animate(onPlay: (controller) => controller.repeat(reverse: true))
         .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.5)), 
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(color: Colors.black.withOpacity(0.3)),
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: Colors.white), 
            onPressed: _logout
          ).animate().fade(delay: 400.ms).scale()
        ],
      ),
      body: Stack(
        children: [
          // Animated Background Gradients
          Positioned(
            top: -100, left: -100,
            child: Container(
              width: 350, height: 350,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentPurple.withOpacity(0.12), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.2, duration: 4.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds),
          ),
          Positioned(
            bottom: -50, right: -100,
            child: Container(
              width: 320, height: 320,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentCyan.withOpacity(0.08), Colors.transparent])),
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
                  _buildStatusHeader(),
                  const SizedBox(height: 24),
                  
                  _sectionTitle("CONTROL MENUS"),
                  const SizedBox(height: 12),
                  
                  _menuCard(
                    title: "MANAGE SLIDESHOW",
                    description: "Upload and schedule images on your smart mirror display.",
                    icon: Icons.photo_library_outlined,
                    color: _accentCyan,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const SlideshowScreen())),
                  ),
                  _menuCard(
                    title: "FAMILY PROFILES",
                    description: "Manage family members, details, and facial biometric profiles.",
                    icon: Icons.people_outline_rounded,
                    color: _accentPurple,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const ManageFamilyMembersScreen())),
                  ),
                  _menuCard(
                    title: "SCHEDULED REMINDERS",
                    description: "Schedule system reminders and alerts on the mirror screen.",
                    icon: Icons.event_note_outlined,
                    color: _accentPink,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const ManageRemindersScreen())),
                  ),
                  
                  const SizedBox(height: 24),
                  _quickAlertPanel(),
                  
                  const SizedBox(height: 28),
                  _sectionTitle("SYSTEM POWER"),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _glassButton(
                          "REBOOT", 
                          Icons.restart_alt_rounded, 
                          _accentCyan, 
                          () => _confirmSystemCommand('reboot', 'Reboot')
                        )
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _glassButton(
                          "SHUTDOWN", 
                          Icons.power_settings_new_rounded, 
                          const Color(0xFFFF4B4B), 
                          () => _confirmSystemCommand('shutdown', 'Shutdown')
                        )
                      ),
                    ],
                  ),
                  const SizedBox(height: 40),
                ].animate(interval: 80.ms).fade(duration: 400.ms).slideY(begin: 0.08, end: 0, curve: Curves.easeOutQuad),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // --- UI COMPONENTS ---
  Widget _buildStatusHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _glassBorder),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "Hello, ${_userEmail.isNotEmpty ? _userEmail : 'User'}!",
                  style: GoogleFonts.orbitron(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  "Control and manage your smart mirror environment.",
                  style: GoogleFonts.outfit(
                    color: Colors.white54,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.greenAccent.withOpacity(0.08),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.greenAccent.withOpacity(0.2)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: Colors.greenAccent,
                    shape: BoxShape.circle,
                  ),
                ).animate(onPlay: (controller) => controller.repeat(reverse: true))
                 .scaleXY(end: 1.3, duration: 1.seconds)
                 .boxShadow(
                   begin: const BoxShadow(color: Colors.transparent, blurRadius: 0),
                   end: const BoxShadow(color: Colors.greenAccent, blurRadius: 6),
                 ),
                const SizedBox(width: 6),
                Text(
                  "ONLINE",
                  style: GoogleFonts.orbitron(
                    color: Colors.greenAccent,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _menuCard({
    required String title,
    required String description,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withOpacity(0.03),
            color.withOpacity(0.05),
          ],
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: InkWell(
            onTap: onTap,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: color.withOpacity(0.3), width: 1.5),
                    ),
                    child: Icon(icon, color: color, size: 28),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: GoogleFonts.orbitron(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          description,
                          style: GoogleFonts.outfit(
                            color: Colors.white54,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(Icons.chevron_right_rounded, color: Colors.white30, size: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _quickAlertPanel() {
    return _glassContainer(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.campaign_outlined, color: _accentCyan, size: 20),
              const SizedBox(width: 8),
              Text(
                "BROADCAST TO MIRROR",
                style: GoogleFonts.orbitron(
                  color: Colors.white70,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.04),
              borderRadius: BorderRadius.circular(15),
              border: Border.all(color: Colors.white.withOpacity(0.08)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _speakController,
                    style: GoogleFonts.outfit(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: "Type message to show on mirror...",
                      hintStyle: GoogleFonts.outfit(color: Colors.white30, fontSize: 13),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    ),
                    onChanged: (text) {
                      setState(() {});
                    },
                  ),
                ),
                _isSendingMessage
                    ? Padding(
                        padding: const EdgeInsets.all(12.0),
                        child: SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: _accentCyan),
                        ),
                      )
                    : IconButton(
                        icon: Icon(Icons.send_rounded, color: _speakController.text.trim().isEmpty ? Colors.white24 : _accentCyan),
                        onPressed: _speakController.text.trim().isEmpty ? null : _sendPuppeteerMessage,
                      ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          Text(
            "QUICK TEMPLATES",
            style: GoogleFonts.orbitron(
              color: Colors.white38,
              fontSize: 10,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _alertTemplates.map((template) {
              return Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: _isSendingMessage ? null : () => _sendDirectAlert(template['label']!),
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.03),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white.withOpacity(0.06)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(template['icon']!, style: const TextStyle(fontSize: 14)),
                        const SizedBox(width: 6),
                        Text(
                          template['label']!,
                          style: GoogleFonts.outfit(
                            color: Colors.white70,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
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
}