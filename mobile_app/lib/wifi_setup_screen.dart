import 'dart:convert';
import 'dart:io';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';

class WifiSetupScreen extends StatefulWidget {
  const WifiSetupScreen({super.key});

  @override
  State<WifiSetupScreen> createState() => _WifiSetupScreenState();
}

class _WifiSetupScreenState extends State<WifiSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _ssidController = TextEditingController();
  final _passwordController = TextEditingController();
  final _ipController = TextEditingController(text: "192.168.4.1"); // Default AP IP address

  bool _isSending = false;
  bool _obscurePassword = true;
  String? _errorMessage;
  String? _successMessage;

  final Color _bgDark = const Color(0xFF07080E);
  final Color _accentCyan = const Color(0xFFFFD86B);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

  Future<void> _provisionWifi() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isSending = true;
      _errorMessage = null;
      _successMessage = null;
    });

    final ssid = _ssidController.text.trim();
    final password = _passwordController.text.trim();
    final ipAddress = _ipController.text.replaceAll(' ', '');

    final client = HttpClient();
    client.connectionTimeout = const Duration(seconds: 10);

    try {
      // Connect to the provisioning API endpoint
      final request = await client.post(ipAddress, 8000, '/api/wifi-setup');
      request.headers.contentType = ContentType.json;
      
      final payload = {
        'ssid': ssid,
        'password': password,
      };
      
      request.write(jsonEncode(payload));
      final response = await request.close();

      if (response.statusCode == 200) {
        final responseBody = await response.transform(utf8.decoder).join();
        final jsonResponse = jsonDecode(responseBody);
        
        setState(() {
          _successMessage = jsonResponse['message'] ?? "Credentials sent successfully! The mirror is connecting...";
        });
      } else {
        setState(() {
          _errorMessage = "Mirror responded with error code: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Failed to connect to the mirror. Please ensure you are connected to the 'ReflectStudio_Setup' Wi-Fi network. (Error: $e)";
      });
    } finally {
      client.close();
      setState(() {
        _isSending = false;
      });
    }
  }

  @override
  void dispose() {
    _ssidController.dispose();
    _passwordController.dispose();
    _ipController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text(
          "WIFI PROVISIONING",
          style: GoogleFonts.orbitron(
            color: Colors.white,
            fontSize: 16,
            letterSpacing: 2,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Stack(
        children: [
          // Background Gradient Glow
          Positioned(
            top: -50,
            right: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [_accentCyan.withOpacity(0.08), Colors.transparent],
                ),
              ),
            ),
          ),
          
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 10),
                    _buildOnboardingCard(),
                    const SizedBox(height: 24),
                    
                    Text(
                      "NETWORK CREDENTIALS",
                      style: GoogleFonts.orbitron(
                        color: Colors.white54,
                        fontSize: 11,
                        letterSpacing: 1.5,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    
                    _buildGlassTextField(
                      controller: _ssidController,
                      label: "Home Wi-Fi Name (SSID)",
                      icon: Icons.wifi_rounded,
                      validator: (value) => value == null || value.trim().isEmpty ? "SSID cannot be empty" : null,
                    ),
                    const SizedBox(height: 16),
                    
                    _buildGlassTextField(
                      controller: _passwordController,
                      label: "Wi-Fi Password",
                      icon: Icons.lock_outline_rounded,
                      obscureText: _obscurePassword,
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscurePassword ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                          color: Colors.white54,
                          size: 20,
                        ),
                        onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                      ),
                      validator: (value) => value == null || value.trim().isEmpty ? "Password cannot be empty" : null,
                    ),
                    const SizedBox(height: 16),
                    
                    _buildGlassTextField(
                      controller: _ipController,
                      label: "Mirror Setup IP Address",
                      icon: Icons.lan_outlined,
                      keyboardType: TextInputType.values[0], // text input
                      validator: (value) => value == null || value.trim().isEmpty ? "IP Address cannot be empty" : null,
                    ),
                    const SizedBox(height: 28),
                    
                    if (_errorMessage != null) ...[
                      _buildStatusBox(
                        title: "Connection Failed",
                        message: _errorMessage!,
                        color: Colors.redAccent,
                        icon: Icons.error_outline_rounded,
                      ),
                      const SizedBox(height: 24),
                    ],
                    
                    if (_successMessage != null) ...[
                      _buildStatusBox(
                        title: "Credentials Transmitted",
                        message: _successMessage!,
                        color: Colors.greenAccent,
                        icon: Icons.check_circle_outline_rounded,
                      ),
                      const SizedBox(height: 24),
                    ],
                    
                    _buildSubmitButton(),
                  ].animate(interval: 50.ms).fade(duration: 300.ms).slideY(begin: 0.05, end: 0),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOnboardingCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.01),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _glassBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.info_outline_rounded, color: _accentCyan, size: 20),
              const SizedBox(width: 8),
              Text(
                "INSTRUCTIONS",
                style: GoogleFonts.orbitron(
                  color: Colors.white70,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            "1. Scan the QR code on the mirror or connect manually to the mirror's Wi-Fi hotspot:\n"
            "   • SSID: ReflectStudio_Setup\n"
            "   • Password: reflectstudio123\n\n"
            "2. Enter your home Wi-Fi details below and tap 'CONNECT MIRROR'.",
            style: GoogleFonts.outfit(
              color: Colors.white54,
              fontSize: 13,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGlassTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool obscureText = false,
    Widget? suffixIcon,
    TextInputType? keyboardType,
    String? Function(String?)? validator,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: _glassWhite,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _glassBorder),
      ),
      child: TextFormField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        validator: validator,
        style: GoogleFonts.outfit(color: Colors.white, fontSize: 14),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: GoogleFonts.outfit(color: Colors.white38, fontSize: 13),
          prefixIcon: Icon(icon, color: _accentCyan.withOpacity(0.7), size: 20),
          suffixIcon: suffixIcon,
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
      ),
    );
  }

  Widget _buildStatusBox({
    required String title,
    required String message,
    required Color color,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.06),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: GoogleFonts.orbitron(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  message,
                  style: GoogleFonts.outfit(
                    color: Colors.white70,
                    fontSize: 12,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSubmitButton() {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: _accentCyan.withOpacity(0.4), width: 1.5),
          ),
          padding: EdgeInsets.zero,
        ),
        onPressed: _isSending ? null : _provisionWifi,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: LinearGradient(
              colors: [
                _accentCyan.withOpacity(0.12),
                _accentCyan.withOpacity(0.04),
              ],
            ),
          ),
          alignment: Alignment.center,
          child: _isSending
              ? const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.5,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : Text(
                  "CONNECT MIRROR",
                  style: GoogleFonts.orbitron(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.5,
                  ),
                ),
        ),
      ),
    );
  }
}
