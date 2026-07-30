import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'email_confirmation_screen.dart'; 

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

  // --- Multi-Angle Image State ---
  final Map<String, Uint8List> _faceAngles = {}; 
  final List<String> _steps = ['front', 'left', 'right'];
  int _currentStepIndex = 0;
  
  final ImagePicker _picker = ImagePicker();
  
  // Loading State
  bool _isLoading = false;
  bool _isPasswordVisible = false;

  // UI Colors
  final Color _accentCyan = const Color(0xFFFFD86B);
  final Color _accentPurple = const Color(0xFFF6C85F);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

  Future<void> _pickImage() async {
    if (_currentStepIndex >= _steps.length && _faceAngles.length == 3) {
      setState(() {
        _currentStepIndex = 0;
        _faceAngles.clear();
      });
    }

    final XFile? returnedImage = await _picker.pickImage(
      source: ImageSource.camera, 
      preferredCameraDevice: CameraDevice.front,
      imageQuality: 70, 
    );

    if (returnedImage != null) {
      final Uint8List bytes = await returnedImage.readAsBytes();
      setState(() {
        _faceAngles[_steps[_currentStepIndex]] = bytes;
        if (_currentStepIndex < _steps.length - 1) {
          _currentStepIndex++;
        } else {
          _currentStepIndex = 3; 
        }
      });
    }
  }

  Future<void> _registerUser() async {
    if (_faceAngles.length < 3) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("⚠️ Please provide all 3 face angles!")));
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
      final String userEmail = _emailController.text.trim();
      final String emailClean = userEmail.replaceAll('@gmail.com', '').replaceAll('.', '_');

      await Amplify.Auth.signUp(
        username: userEmail,
        password: _passController.text,
        options: SignUpOptions(
          userAttributes: {
            AuthUserAttributeKey.email: userEmail,
            AuthUserAttributeKey.name: _nameController.text.trim(),
          },
        ),
      );

      for (String angle in _faceAngles.keys) {
        final String pathName = 'public/face_entries/${emailClean}_Owner_Self_$angle.jpg';
        
        await Amplify.Storage.uploadData(
          data: StorageDataPayload.bytes(_faceAngles[angle]!),
          path: StoragePath.fromString(pathName),
        ).result;
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("✅ Account Created! Sending Verification Code..."), backgroundColor: Colors.green)
        );

        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => EmailConfirmationScreen(email: userEmail),
          ),
        );
      }
    } on AuthException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: ${e.message}"), backgroundColor: Colors.red));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    String instruction = _currentStepIndex == 0 ? "Look Straight" : 
                         _currentStepIndex == 1 ? "Turn Left" : 
                         _currentStepIndex == 2 ? "Turn Right" : "Captured!";

    return Scaffold(
      backgroundColor: _bgDark,
      body: Stack(
        children: [
          Positioned(
            top: -100, right: -100,
            child: Container(
              width: 320, height: 320,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(colors: [_accentPurple.withOpacity(0.12), Colors.transparent]),
              ),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.25, duration: 4.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds),
          ),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 15),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
                    onPressed: () => Navigator.pop(context),
                  ),
                  const SizedBox(height: 10),
                  Text("BIOMETRIC PROFILE", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold, letterSpacing: 2))
                    .animate(onPlay: (controller) => controller.repeat(reverse: true))
                    .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.4)),
                  Text("Register your face for ReflectStudio", style: GoogleFonts.outfit(color: Colors.white38, fontSize: 13)),

                  const SizedBox(height: 28),

                  // Guided Camera UI
                  Center(
                    child: Column(
                      children: [
                        GestureDetector(
                          onTap: _pickImage,
                          child: Container(
                            height: 120, width: 120,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _glassWhite,
                              border: Border.all(
                                color: _faceAngles.length == 3 ? _accentCyan : _glassBorder, 
                                width: 2
                              ),
                              boxShadow: _faceAngles.length == 3 ? [BoxShadow(color: _accentCyan.withOpacity(0.15), blurRadius: 15)] : [],
                            ),
                            child: _faceAngles[_steps[_currentStepIndex == 3 ? 0 : _currentStepIndex]] != null
                                ? ClipOval(child: Image.memory(_faceAngles[_steps[_currentStepIndex == 3 ? 0 : _currentStepIndex]]!, fit: BoxFit.cover))
                                : Icon(Icons.face_retouching_natural_rounded, color: _accentCyan, size: 40),
                          ).animate(target: _faceAngles.length == 3 ? 1 : 0).shimmer(duration: 1.seconds, color: Colors.white),
                        ),
                        const SizedBox(height: 12),
                        Text(instruction.toUpperCase(), style: GoogleFonts.orbitron(color: _accentCyan, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.2))
                          .animate(onPlay: (controller) => controller.repeat(reverse: true)).fadeIn().fadeOut(duration: 1.seconds),
                        
                        const SizedBox(height: 8),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: List.generate(3, (index) => Container(
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            width: 6, height: 6,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _faceAngles.containsKey(_steps[index]) ? _accentCyan : Colors.white10,
                            ),
                          )),
                        )
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 28),

                  _buildLabel("Full Name"),
                  _buildGlassTextField(controller: _nameController, hint: "Enter your full name"),
                  
                  const SizedBox(height: 15),

                  _buildLabel("Email Address"),
                  _buildGlassTextField(controller: _emailController, hint: "Enter your email"),

                  const SizedBox(height: 15),

                  _buildLabel("Password"),
                  _buildGlassTextField(controller: _passController, hint: "Create a password", isPassword: true),

                  const SizedBox(height: 15),

                  _buildLabel("Confirm Password"),
                  _buildGlassTextField(controller: _confirmPassController, hint: "Confirm your password", isPassword: true),

                  const SizedBox(height: 35),

                  Container(
                    width: double.infinity, height: 55,
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
                      onPressed: _isLoading ? null : _registerUser,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      child: _isLoading 
                        ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text("CREATE PROFILE", style: GoogleFonts.orbitron(fontSize: 15, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
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

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6.0, left: 5),
      child: Text(text, style: GoogleFonts.orbitron(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1)),
    );
  }

  Widget _buildGlassTextField({required TextEditingController controller, required String hint, bool isPassword = false}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03), 
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _glassBorder),
      ),
      child: TextField(
        controller: controller,
        obscureText: isPassword && !_isPasswordVisible,
        style: GoogleFonts.outfit(color: Colors.white, fontSize: 15),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: GoogleFonts.outfit(color: Colors.white24, fontSize: 14),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          border: InputBorder.none,
          suffixIcon: isPassword 
            ? IconButton(
                icon: Icon(_isPasswordVisible ? Icons.visibility_rounded : Icons.visibility_off_rounded, color: Colors.white30, size: 20),
                onPressed: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
              )
            : null,
        ),
      ),
    );
  }
}