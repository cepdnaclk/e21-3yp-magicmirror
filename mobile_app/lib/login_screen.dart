import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'home_screen.dart';
import 'signup_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _userController = TextEditingController(); 
  final TextEditingController _passController = TextEditingController();

  final Color _accentCyan = const Color(0xFFFFD86B);
  final Color _accentPurple = const Color(0xFFF6C85F);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);
  
  bool _isLoading = false;

  Future<void> _login() async {
    if (_userController.text.isEmpty || _passController.text.isEmpty) return;

    setState(() => _isLoading = true);

    try {
      final session = await Amplify.Auth.fetchAuthSession();
      if (session.isSignedIn) {
        if (mounted) {
          Navigator.pushReplacement(
            context, 
            MaterialPageRoute(builder: (context) => const HomeScreen()),
          );
        }
        return; 
      }

      final SignInResult res = await Amplify.Auth.signIn(
        username: _userController.text.trim(),
        password: _passController.text,
      );

      if (res.isSignedIn && mounted) {
        Navigator.pushReplacement(
          context, 
          MaterialPageRoute(builder: (context) => const HomeScreen()),
        );
      } else if (res.nextStep.signInStep == AuthSignInStep.confirmSignUp) {
         if(mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please verify your email code first!")));
      }
    } on AuthException catch (e) {
      if (e.message.contains("already signed in")) {
        if (mounted) {
          Navigator.pushReplacement(
            context, 
            MaterialPageRoute(builder: (context) => const HomeScreen()),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(e.message), backgroundColor: Colors.redAccent)
          );
        }
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
          // Animated Background Gradient 1
          Positioned(
            top: -100, right: -100,
            child: Container(
              width: 320, height: 320,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentPurple.withOpacity(0.12), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.25, duration: 4.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds),
          ),
          // Animated Background Gradient 2
          Positioned(
            bottom: -50, left: -100,
            child: Container(
              width: 320, height: 320,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentCyan.withOpacity(0.08), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.35, duration: 5.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds, delay: 1.seconds),
          ),
          
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(30),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    height: 110, width: 110,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _glassWhite,
                      border: Border.all(color: _accentCyan.withOpacity(0.2)),
                      boxShadow: [BoxShadow(color: _accentPurple.withOpacity(0.15), blurRadius: 20)],
                    ),
                    child: ClipOval(
                      child: Image.asset(
                         'assets/images/head_logo.png',
                         fit: BoxFit.contain,
                         errorBuilder: (context, error, stackTrace) => 
                           Icon(Icons.face_unlock_rounded, color: _accentCyan, size: 50),
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),
                  Text("REFLECTSTUDIO", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 28, letterSpacing: 4, fontWeight: FontWeight.bold))
                    .animate(onPlay: (controller) => controller.repeat(reverse: true))
                    .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.4)),
                  Text("INTELLIGENT MIRROR SYSTEM", style: GoogleFonts.outfit(color: Colors.white38, fontSize: 11, letterSpacing: 2, fontWeight: FontWeight.w500)),
                  
                  const SizedBox(height: 40),

                  _glassContainer(
                    child: Column(
                      children: [
                        _customTextField(_userController, Icons.mail_outline_rounded, "Email Address"),
                        const SizedBox(height: 18),
                        _customTextField(_passController, Icons.lock_outline_rounded, "Password", isPassword: true),
                        const SizedBox(height: 28),
                        
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
                            onPressed: _isLoading ? null : _login,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.transparent,
                              shadowColor: Colors.transparent,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                            ),
                            child: _isLoading 
                             ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                             : Text("ENTER SYSTEM", style: GoogleFonts.orbitron(fontSize: 15, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                          ),
                        ).animate(onPlay: (controller) => controller.repeat(reverse: true))
                         .shimmer(duration: 3.seconds, color: Colors.white.withOpacity(0.2)),
                      ],
                    ),
                  ),

                  const SizedBox(height: 30),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text("Don't have an account? ", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 14)),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const SignUpScreen()),
                          );
                        },
                        child: Text("Create One", style: GoogleFonts.outfit(color: _accentCyan, fontWeight: FontWeight.bold, fontSize: 14)),
                      ),
                    ],
                  ),
                ].animate(interval: 80.ms).fade(duration: 450.ms).slideY(begin: 0.08, end: 0, curve: Curves.easeOutQuad),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _glassContainer({required Widget child}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02), 
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _glassBorder),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 15, spreadRadius: 2)],
      ),
      child: child,
    );
  }

  Widget _customTextField(TextEditingController controller, IconData icon, String hint, {bool isPassword = false}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.06)),
      ),
      child: TextField(
        controller: controller,
        obscureText: isPassword,
        style: GoogleFonts.outfit(color: Colors.white, fontSize: 15),
        decoration: InputDecoration(
          prefixIcon: Icon(icon, color: _accentCyan.withOpacity(0.6), size: 20),
          hintText: hint,
          hintStyle: GoogleFonts.outfit(color: Colors.white24, fontSize: 14),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
      ),
    );
  }
}