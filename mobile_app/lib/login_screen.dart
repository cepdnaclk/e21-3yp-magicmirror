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

  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);
  final Color _glassWhite = Colors.white.withOpacity(0.05);
  final Color _glassBorder = Colors.white.withOpacity(0.1);
  
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
              width: 300, height: 300,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentColor.withOpacity(0.15), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.2, duration: 4.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds),
          ),
          // Animated Background Gradient 2
          Positioned(
            bottom: -50, left: -100,
            child: Container(
              width: 300, height: 300,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [Colors.cyan.withOpacity(0.1), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.3, duration: 5.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds, delay: 1.seconds),
          ),
          
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(30),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    height: 120, width: 120,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _glassWhite,
                      boxShadow: [BoxShadow(color: _accentColor.withOpacity(0.2), blurRadius: 20)],
                    ),
                    child: ClipOval(
                      child: Image.asset(
                         'assets/images/head_logo.png',
                         fit: BoxFit.contain,
                         errorBuilder: (context, error, stackTrace) => 
                           Icon(Icons.lock_outline, color: _accentColor, size: 60),
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),
                  Text("MAGIC MIRROR", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 32, letterSpacing: 4, fontWeight: FontWeight.bold))
                    .animate(onPlay: (controller) => controller.repeat(reverse: true))
                    .shimmer(duration: 2.seconds, color: _accentColor.withOpacity(0.5)),
                  Text("SECURE ACCESS", style: GoogleFonts.outfit(color: Colors.white54, fontSize: 12, letterSpacing: 2)),
                  
                  const SizedBox(height: 50),

                  _glassContainer(
                    child: Column(
                      children: [
                        _customTextField(_userController, Icons.person, "Email Address"),
                        const SizedBox(height: 20),
                        _customTextField(_passController, Icons.key, "Password", isPassword: true),
                        const SizedBox(height: 30),
                        
                        SizedBox(
                          width: double.infinity, height: 55,
                          child: ElevatedButton(
                            onPressed: _isLoading ? null : _login,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _accentColor,
                              foregroundColor: Colors.black,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                              elevation: 10,
                              shadowColor: _accentColor.withOpacity(0.5),
                            ),
                            child: _isLoading 
                             ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                             : Text("ENTER SYSTEM", style: GoogleFonts.orbitron(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1)),
                          ),
                        ).animate(onPlay: (controller) => controller.repeat(reverse: true))
                         .boxShadow(
                           begin: BoxShadow(color: _accentColor.withOpacity(0.2), blurRadius: 5, spreadRadius: 0),
                           end: BoxShadow(color: _accentColor.withOpacity(0.6), blurRadius: 15, spreadRadius: 2),
                           duration: 2.seconds,
                         ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 30),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text("Don't have an account? ", style: GoogleFonts.outfit(color: Colors.white54)),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const SignUpScreen()),
                          );
                        },
                        child: Text("Create One", style: GoogleFonts.outfit(color: _accentColor, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                ].animate(interval: 100.ms).fade(duration: 500.ms).slideY(begin: 0.1, end: 0, curve: Curves.easeOutQuad),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _glassContainer({required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(30),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3), 
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 20, spreadRadius: 5)],
      ),
      child: child,
    );
  }

  Widget _customTextField(TextEditingController controller, IconData icon, String hint, {bool isPassword = false}) {
    return TextField(
      controller: controller,
      obscureText: isPassword,
      style: GoogleFonts.outfit(color: Colors.white),
      decoration: InputDecoration(
        prefixIcon: Icon(icon, color: Colors.white54),
        hintText: hint,
        hintStyle: GoogleFonts.outfit(color: Colors.white24),
        filled: true,
        fillColor: Colors.white.withOpacity(0.05),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: BorderSide(color: _accentColor.withOpacity(0.5))),
      ),
    );
  }
}