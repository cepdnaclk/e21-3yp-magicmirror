import 'dart:typed_data'; 
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'database_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final DatabaseService _db = DatabaseService();
  
  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _pinCtrl = TextEditingController();

  String _selectedRole = 'Family'; 
  final List<String> _roles = ['Admin', 'Family', 'Guest'];

  String _selectedTheme = 'Cyberpunk';
  final List<String> _themes = ['Cyberpunk', 'Shrek', 'Minimalist'];

  Uint8List? _photoBytes; 
  bool _isLoading = false;

  final Color _accentCyan = const Color(0xFFFFD86B);
  final Color _accentPurple = const Color(0xFFF6C85F);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

  Future<void> _takePhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera, preferredCameraDevice: CameraDevice.front);
    
    if (picked != null) {
      final bytes = await picked.readAsBytes();
      setState(() => _photoBytes = bytes);
    }
  }

  Future<void> _submit() async {
    if (_photoBytes == null || _nameCtrl.text.isEmpty || _pinCtrl.text.length != 4) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please fill all fields & 4-digit PIN!")));
      return;
    }
    
    setState(() => _isLoading = true);
    
    try {
      await _db.uploadProfile(
        name: _nameCtrl.text, 
        role: _selectedRole, 
        pin: _pinCtrl.text,       
        theme: _selectedTheme,    
        photoBytes: _photoBytes! 
      );
      
      if(mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("User Created Successfully!")));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text("Create Profile", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2))
          .animate(onPlay: (controller) => controller.repeat(reverse: true))
          .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.5)), 
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Stack(
        children: [
          Positioned(
            top: -100, right: -100,
            child: Container(
              width: 320, height: 320,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentPurple.withOpacity(0.12), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.25, duration: 4.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds),
          ),
          
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(25),
              child: Column(
                children: [
                  // 1. PHOTO
                  GestureDetector(
                    onTap: _takePhoto,
                    child: Container(
                      height: 130, width: 130,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _glassWhite,
                        border: Border.all(color: _photoBytes != null ? _accentCyan : _glassBorder, width: 2),
                        boxShadow: _photoBytes != null ? [BoxShadow(color: _accentCyan.withOpacity(0.15), blurRadius: 15)] : [],
                      ),
                      child: _photoBytes != null
                        ? ClipOval(child: Image.memory(_photoBytes!, fit: BoxFit.cover))
                        : Icon(Icons.camera_alt_rounded, size: 36, color: _accentCyan),
                    ).animate(target: _photoBytes != null ? 1 : 0).shimmer(duration: 1.seconds, color: Colors.white),
                  ),
                  const SizedBox(height: 10),
                  Text("Tap for Selfie", style: GoogleFonts.outfit(color: Colors.white38, fontSize: 13)),

                  const SizedBox(height: 30),

                  // 2. NAME
                  _buildTextField(label: "Name", hint: "e.g. John Doe", controller: _nameCtrl, icon: Icons.person_rounded),
                  
                  const SizedBox(height: 20),

                  // 3. PIN CODE
                  _buildTextField(
                    label: "4-Digit PIN", 
                    hint: "Backup Access",
                    controller: _pinCtrl, 
                    icon: Icons.lock_rounded, 
                    isNumber: true
                  ),

                  const SizedBox(height: 20),

                  // 4. DROPDOWNS
                  Row(
                    children: [
                      Expanded(child: _buildDropdown("Role", _selectedRole, _roles, (val) => setState(() => _selectedRole = val!))),
                      const SizedBox(width: 15),
                      Expanded(child: _buildDropdown("Theme", _selectedTheme, _themes, (val) => setState(() => _selectedTheme = val!))),
                    ],
                  ),

                  const SizedBox(height: 50),

                  // 5. REGISTER BUTTON
                  Container(
                    width: double.infinity,
                    height: 55,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      gradient: LinearGradient(
                        colors: [_accentPurple, _accentCyan],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: _accentCyan.withOpacity(0.2),
                          blurRadius: 12,
                          spreadRadius: 0,
                          offset: const Offset(0, 4),
                        )
                      ],
                    ),
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      onPressed: _isLoading ? null : _submit,
                      child: _isLoading 
                        ? const CircularProgressIndicator(color: Colors.white) 
                        : Text("REGISTER USER", style: GoogleFonts.orbitron(fontSize: 15, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                    ),
                  ).animate(onPlay: (controller) => controller.repeat(reverse: true))
                   .shimmer(duration: 3.seconds, color: Colors.white.withOpacity(0.2)),
                ].animate(interval: 80.ms).fade(duration: 450.ms).slideY(begin: 0.08, end: 0, curve: Curves.easeOutQuad),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTextField({required String label, required String hint, required TextEditingController controller, required IconData icon, bool isNumber = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8.0, left: 5),
          child: Text(label, style: GoogleFonts.orbitron(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1)),
        ),
        Container(
          decoration: BoxDecoration(
            color: _glassWhite, 
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: _glassBorder),
          ),
          child: TextField(
            controller: controller,
            keyboardType: isNumber ? TextInputType.number : TextInputType.text,
            maxLength: isNumber ? 4 : null,
            style: GoogleFonts.outfit(color: Colors.white, fontSize: 15),
            decoration: InputDecoration(
              hintText: hint,
              hintStyle: GoogleFonts.outfit(color: Colors.white24, fontSize: 14),
              prefixIcon: Icon(icon, color: Colors.white54),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              border: InputBorder.none,
              counterText: "",
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDropdown(String title, String value, List<String> items, Function(String?) onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8.0, left: 5),
          child: Text(title, style: GoogleFonts.orbitron(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1)),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: _glassWhite, 
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: _glassBorder),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: value,
              dropdownColor: _bgDark,
              isExpanded: true,
              style: GoogleFonts.outfit(color: Colors.white, fontSize: 15),
              items: items.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
              onChanged: onChanged,
            ),
          ),
        ),
      ],
    );
  }
}