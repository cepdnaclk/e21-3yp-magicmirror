import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'email_confirmation_screen.dart'; // අලුත් Screen එක අනිවාර්යයෙන්ම import කරන්න

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
  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);
  final Color _glassWhite = Colors.white.withOpacity(0.05);
  final Color _glassBorder = Colors.white.withOpacity(0.1);

  // --- 1. GUIDED PICK IMAGE ---
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

  // --- 2. SECURE REGISTRATION & NAVIGATION ---
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

      // 1. Create AWS Cognito User (Status: UNCONFIRMED)
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

      // 2. Upload 3 Images to S3
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

        // --- වැදගත්: මෙතැනදී කෙලින්ම OTP Screen එකට යනවා ---
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
                  Text("Biometric Profile", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold)),
                  Text("Register your face for ReflectStudio", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 14)),

                  const SizedBox(height: 30),

                  // Guided Camera UI
                  Center(
                    child: Column(
                      children: [
                        GestureDetector(
                          onTap: _pickImage,
                          child: Container(
                            height: 130, width: 130,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _glassWhite,
                              border: Border.all(
                                color: _faceAngles.length == 3 ? _accentColor : _glassBorder, 
                                width: 2
                              ),
                              boxShadow: _faceAngles.length == 3 ? [BoxShadow(color: _accentColor.withOpacity(0.2), blurRadius: 20)] : [],
                            ),
                            child: _faceAngles[_steps[_currentStepIndex == 3 ? 0 : _currentStepIndex]] != null
                                ? ClipOval(child: Image.memory(_faceAngles[_steps[_currentStepIndex == 3 ? 0 : _currentStepIndex]]!, fit: BoxFit.cover))
                                : Icon(Icons.camera_front_rounded, color: _accentColor, size: 45),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(instruction.toUpperCase(), style: GoogleFonts.orbitron(color: _accentColor, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
                        
                        const SizedBox(height: 10),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: List.generate(3, (index) => Container(
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            width: 8, height: 8,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _faceAngles.containsKey(_steps[index]) ? _accentColor : Colors.white10,
                            ),
                          )),
                        )
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 30),

                  _buildLabel("Full Name"),
                  _buildGlassTextField(controller: _nameController, hint: "Enter your full name"),
                  
                  const SizedBox(height: 15),

                  _buildLabel("Email address"),
                  _buildGlassTextField(controller: _emailController, hint: "Enter your email"),

                  const SizedBox(height: 15),

                  _buildLabel("Password"),
                  _buildGlassTextField(controller: _passController, hint: "Create a password", isPassword: true),

                  const SizedBox(height: 15),

                  _buildLabel("Confirm Password"),
                  _buildGlassTextField(controller: _confirmPassController, hint: "Confirm your password", isPassword: true),

                  const SizedBox(height: 40),

                  SizedBox(
                    width: double.infinity, height: 55,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _registerUser,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _accentColor,
                        foregroundColor: Colors.black,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                      ),
                      child: _isLoading 
                        ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                        : Text("CREATE PROFILE", style: GoogleFonts.orbitron(fontSize: 16, fontWeight: FontWeight.bold)),
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
      padding: const EdgeInsets.only(bottom: 6.0, left: 5),
      child: Text(text, style: GoogleFonts.orbitron(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildGlassTextField({required TextEditingController controller, required String hint, bool isPassword = false}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.08), 
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: TextField(
        controller: controller,
        obscureText: isPassword && !_isPasswordVisible,
        style: GoogleFonts.outfit(color: Colors.white),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: GoogleFonts.outfit(color: Colors.white24),
          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
          border: InputBorder.none,
          suffixIcon: isPassword 
            ? IconButton(
                icon: Icon(_isPasswordVisible ? Icons.visibility : Icons.visibility_off, color: Colors.white54),
                onPressed: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
              )
            : null,
        ),
      ),
    );
  }
}