import 'dart:ui'; // Required for Glass effect (BackdropFilter)
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'database_service.dart';
import 'slideshow_screen.dart';
// import 'profile_screen.dart'; // <--- REMOVED: No longer needed

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final DatabaseService _db = DatabaseService();
  final TextEditingController _speakController = TextEditingController();
  
  // --- STATES ---
  bool _isFanOn = false;
  // New States for Modules
  bool _showClock = true;
  bool _showNews = true;
  bool _showCalendar = false;

  // --- THEME COLORS ---
  final Color _accentColor = const Color(0xFFC4D300); // Neon Gold
  final Color _bgDark = const Color(0xFF0A0B10);      // Deep Black
  final Color _glassWhite = Colors.white.withOpacity(0.05);
  final Color _glassBorder = Colors.white.withOpacity(0.1);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true, 
      
      // --- APP BAR ---
      appBar: AppBar(
        title: Text("MAGIC MIRROR", 
          style: GoogleFonts.orbitron(
            color: Colors.white, 
            fontSize: 24, 
            letterSpacing: 2, 
            fontWeight: FontWeight.bold
          )
        ),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(color: Colors.black.withOpacity(0.2)),
          ),
        ),
        // actions: [] <--- REMOVED THE BUTTON HERE
      ),

      // --- BODY WITH BACKGROUND GLOW ---
      body: Stack(
        children: [
          // 1. Background Glow Animation
          Positioned(
            top: -100,
            left: -100,
            child: Container(
              width: 400,
              height: 400,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [_accentColor.withOpacity(0.15), Colors.transparent],
                ),
              ),
            ),
          ),

          // 2. Main Content
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  
                  // --- 1. SENSOR DASHBOARD ---
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

                  // --- 2. SMART MODULES (NEW) ---
                  _sectionTitle("MIRROR MODULES"),
                  const SizedBox(height: 12),
                  // We use a Column of switches for better control
                  Column(
                    children: [
                      _glassSwitchTile("Clock Widget", Icons.access_time, _showClock, (val) {
                        setState(() => _showClock = val);
                        _db.sendCommand('module_clock', val.toString());
                      }),
                      const SizedBox(height: 12),
                      _glassSwitchTile("Live News Feed", Icons.newspaper, _showNews, (val) {
                        setState(() => _showNews = val);
                        _db.sendCommand('module_news', val.toString());
                      }),
                      const SizedBox(height: 12),
                      _glassSwitchTile("Calendar Events", Icons.calendar_month, _showCalendar, (val) {
                        setState(() => _showCalendar = val);
                        _db.sendCommand('module_calendar', val.toString());
                      }),
                    ],
                  ),

                  const SizedBox(height: 32),

                  // --- 3. FAN CONTROL ---
                  _sectionTitle("THE WIND GUARDIAN"),
                  const SizedBox(height: 12),
                  _glassSwitchTile("Fan Status", Icons.wind_power, _isFanOn, (val) {
                    setState(() => _isFanOn = val);
                    _db.sendCommand('fan', val.toString()); 
                  }),

                  const SizedBox(height: 32),

                  // --- 4. THE PUPPETEER ---
                  _sectionTitle("THE PUPPETEER"),
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
                              hintText: "Type what Shrek should say...",
                              hintStyle: GoogleFonts.outfit(color: Colors.white38),
                              border: InputBorder.none,
                              contentPadding: const EdgeInsets.symmetric(horizontal: 15),
                            ),
                          ),
                        ),
                        Container(
                          margin: const EdgeInsets.only(right: 5),
                          decoration: BoxDecoration(
                            color: _accentColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: IconButton(
                            icon: Icon(Icons.send_rounded, color: _accentColor),
                            onPressed: () {
                              if (_speakController.text.isNotEmpty) {
                                _db.sendCommand('speak', _speakController.text);
                                _speakController.clear();
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text("Sent to Mirror!", style: GoogleFonts.outfit()),
                                    backgroundColor: Colors.grey[900],
                                    behavior: SnackBarBehavior.floating,
                                  )
                                );
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 32),

                  // --- 5. SYSTEM POWER (NEW) ---
                  _sectionTitle("SYSTEM POWER"),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _glassButton("REBOOT", Icons.restart_alt, Colors.cyan, () {
                          _db.sendCommand('system', 'reboot');
                        }),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _glassButton("SHUTDOWN", Icons.power_settings_new, Colors.redAccent, () {
                          _db.sendCommand('system', 'shutdown');
                        }),
                      ),
                    ],
                  ),

                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 55,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.push(context, MaterialPageRoute(builder: (context) => const SlideshowScreen()));
                      },
                      icon: const Icon(Icons.photo_library, color: Colors.black),
                      label: Text("MANAGE SLIDESHOW", style: GoogleFonts.orbitron(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.black)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _accentColor,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                      ),
                    ),
                  ),

                  const SizedBox(height: 50), // Bottom padding
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // --- REUSABLE WIDGETS ---

  Widget _sectionTitle(String text) {
    return Text(text, 
      style: GoogleFonts.orbitron(
        color: Colors.white54, 
        fontSize: 12, 
        letterSpacing: 2, 
        fontWeight: FontWeight.bold
      )
    );
  }

  Widget _glassContainer({required Widget child, EdgeInsetsGeometry? padding}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: padding ?? const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: _glassWhite,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: _glassBorder),
          ),
          child: child,
        ),
      ),
    );
  }

  // A reusable switch tile for Modules & Fan
  Widget _glassSwitchTile(String title, IconData icon, bool value, Function(bool) onChanged) {
    return _glassContainer(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Icon(icon, color: Colors.white54, size: 20),
              const SizedBox(width: 12),
              Text(title, style: GoogleFonts.outfit(color: Colors.white, fontSize: 16)),
            ],
          ),
          Transform.scale(
            scale: 0.9,
            child: Switch(
              value: value,
              activeColor: Colors.black,
              activeTrackColor: _accentColor,
              inactiveThumbColor: Colors.grey,
              inactiveTrackColor: Colors.grey[800],
              onChanged: onChanged,
            ),
          ),
        ],
      ),
    );
  }

  Widget _glassButton(String label, IconData icon, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: _glassContainer(
        padding: const EdgeInsets.symmetric(vertical: 20),
        child: Column(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 8),
            Text(label, style: GoogleFonts.orbitron(color: color, fontSize: 12, fontWeight: FontWeight.bold)),
          ],
        ),
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
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(height: 16),
            Text(value, 
              style: GoogleFonts.outfit(
                color: Colors.white, 
                fontSize: 28, 
                fontWeight: FontWeight.w600
              )
            ),
            Text(label, 
              style: GoogleFonts.outfit(
                color: Colors.white54, 
                fontSize: 12, 
                letterSpacing: 1
              )
            ),
          ],
        ),
      ),
    );
  }
}