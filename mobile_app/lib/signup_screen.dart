import 'dart:typed_data';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({super.key});

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  // Controllers
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  final _confirmPassController = TextEditingController();

  // Image State
  Uint8List? _imageBytes; 
  final ImagePicker _picker = ImagePicker();
  
  // Loading State
  bool _isLoading = false;

  // UI Colors
  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);
  final Color _glassWhite = Colors.white.withOpacity(0.05);
  final Color _glassBorder = Colors.white.withOpacity(0.1);

  bool _isPasswordVisible = false;

  // --- 1. PICK IMAGE ---
  Future<void> _pickImage() async {
    final XFile? returnedImage = await _picker.pickImage(
      source: ImageSource.camera, 
      imageQuality: 50, 
    );

    if (returnedImage != null) {
      final Uint8List bytes = await returnedImage.readAsBytes();
      setState(() {
        _imageBytes = bytes;
      });
    }
  }

  // --- 2. SECURE REGISTRATION ---
  Future<void> _registerUser() async {
    // A. Validation
    if (_imageBytes == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("⚠️ Please take a photo first!")));
      return;
    }
    if (_nameController.text.isEmpty || _emailController.text.isEmpty || _passController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("⚠️ All fields are required!")));
      return;
    }
    if (_passController.text != _confirmPassController.text) {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("⚠️ Passwords do not match!")));
       return;
    }

    setState(() => _isLoading = true);

    try {
      final supabase = Supabase.instance.client;

      // B. Create Auth User (The Secure Step)
      final AuthResponse res = await supabase.auth.signUp(
        email: _emailController.text.trim(),
        password: _passController.text,
      );

      final User? user = res.user;

      if (user != null) {
        // C. Upload Image using the User's Secure ID
        final String path = '${user.id}/face_entry.jpg';
        
        await supabase.storage.from('face_entries').uploadBinary(
          path,
          _imageBytes!,
          fileOptions: const FileOptions(upsert: true),
        );

        // D. Get Public URL
        final String imageUrl = supabase.storage.from('face_entries').getPublicUrl(path);

        // E. Save Profile Data (Linked to Auth ID)
        await supabase.from('users').insert({
          'id': user.id, // <--- IMPORTANT: Links this row to the Auth User
          'name': _nameController.text.trim(),
          'email': _emailController.text.trim(),
          'photo_url': imageUrl,
          'created_at': DateTime.now().toIso8601String(),
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text("✅ Account Created! You can now login."),
              backgroundColor: Colors.green,
            )
          );
          Navigator.pop(context); // Return to login screen
        }
      }
    } on AuthException catch (e) {
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Auth Error: ${e.message}"), backgroundColor: Colors.red)
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red)
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      body: Stack(
        children: [
          // Background Glow
          Positioned(
            top: -100, right: -100,
            child: Container(
              width: 300, height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(colors: [_accentColor.withOpacity(0.15), Colors.transparent]),
              ),
            ),
          ),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.white),
                    onPressed: () => Navigator.pop(context),
                  ),
                  const SizedBox(height: 10),
                  Text("Biometric Profile", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
                  Text("Upload your face for Magic Mirror access", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 14)),

                  const SizedBox(height: 30),

                  // Camera Widget
                  Center(
                    child: GestureDetector(
                      onTap: _pickImage,
                      child: Container(
                        height: 120, width: 120,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: _glassWhite,
                          border: Border.all(color: _imageBytes != null ? _accentColor : _glassBorder, width: 2),
                          boxShadow: _imageBytes != null ? [BoxShadow(color: _accentColor.withOpacity(0.3), blurRadius: 20, spreadRadius: 5)] : [],
                        ),
                        child: _imageBytes != null
                            ? ClipOval(child: Image.memory(_imageBytes!, fit: BoxFit.cover))
                            : Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.camera_alt_outlined, color: _accentColor, size: 40),
                                  const SizedBox(height: 5),
                                  Text("Add Photo", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 10)),
                                ],
                              ),
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 40),

                  _buildLabel("Full Name"),
                  _buildGlassTextField(controller: _nameController, hint: "Enter your full name"),
                  
                  const SizedBox(height: 20),

                  _buildLabel("Email address"),
                  _buildGlassTextField(controller: _emailController, hint: "Enter your email"),

                  const SizedBox(height: 20),

                  _buildLabel("Password"),
                  _buildGlassTextField(controller: _passController, hint: "Create a password", isPassword: true),

                  const SizedBox(height: 20),

                  _buildLabel("Confirm Password"),
                  _buildGlassTextField(controller: _confirmPassController, hint: "Confirm your password", isPassword: true),

                  const SizedBox(height: 50),

                  // Register Button
                  SizedBox(
                    width: double.infinity, height: 55,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _registerUser,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _accentColor,
                        foregroundColor: Colors.black,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                        elevation: 10,
                        shadowColor: _accentColor.withOpacity(0.4),
                      ),
                      child: _isLoading 
                        ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                        : Text("REGISTER USER", style: GoogleFonts.orbitron(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1)),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0, left: 5),
      child: Text(text, style: GoogleFonts.orbitron(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1)),
    );
  }

  Widget _buildGlassTextField({required TextEditingController controller, required String hint, bool isPassword = false}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(15),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(
            color: _glassWhite,
            borderRadius: BorderRadius.circular(15),
            border: Border.all(color: _glassBorder),
          ),
          child: TextField(
            controller: controller,
            obscureText: isPassword && !_isPasswordVisible,
            style: GoogleFonts.outfit(color: Colors.white),
            decoration: InputDecoration(
              hintText: hint,
              hintStyle: GoogleFonts.outfit(color: Colors.white24),
              contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
              border: InputBorder.none,
              suffixIcon: isPassword 
                ? IconButton(
                    icon: Icon(_isPasswordVisible ? Icons.visibility : Icons.visibility_off, color: Colors.white54),
                    onPressed: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
                  )
                : null,
            ),
          ),
        ),
      ),
    );
  }
}