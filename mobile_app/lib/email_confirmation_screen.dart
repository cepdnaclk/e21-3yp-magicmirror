import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'login_screen.dart';

class EmailConfirmationScreen extends StatefulWidget {
  final String email;
  const EmailConfirmationScreen({super.key, required this.email});

  @override
  State<EmailConfirmationScreen> createState() => _EmailConfirmationScreenState();
}

class _EmailConfirmationScreenState extends State<EmailConfirmationScreen> {
  final _codeController = TextEditingController();
  bool _isLoading = false;

  final Color _accentCyan = const Color(0xFF00F0FF);
  final Color _accentPurple = const Color(0xFF9E00FF);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

  Future<void> _verifyCode() async {
    if (_codeController.text.trim().isEmpty) return;

    setState(() => _isLoading = true);

    try {
      final result = await Amplify.Auth.confirmSignUp(
        username: widget.email,
        confirmationCode: _codeController.text.trim(),
      );

      if (result.isSignUpComplete && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("✅ Email Verified! You can now log in."), backgroundColor: Colors.green)
        );
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (context) => const LoginScreen()),
          (route) => false,
        );
      }
    } on AuthException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("❌ Verification Error: ${e.message}"), backgroundColor: Colors.red)
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
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Verify Email", 
                    style: GoogleFonts.orbitron(color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold, letterSpacing: 1.5))
                    .animate(onPlay: (controller) => controller.repeat(reverse: true))
                    .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.5)),
                  const SizedBox(height: 10),
                  Text("Enter the 6-digit code sent to ${widget.email}", 
                    style: GoogleFonts.outfit(color: Colors.white38, fontSize: 13)),
                  
                  const SizedBox(height: 30),

                  // OTP Input Field
                  Container(
                    decoration: BoxDecoration(
                      color: _glassWhite, 
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: _glassBorder),
                    ),
                    child: TextField(
                      controller: _codeController,
                      keyboardType: TextInputType.number,
                      textAlign: TextAlign.center,
                      style: GoogleFonts.orbitron(color: _accentCyan, fontSize: 24, letterSpacing: 10),
                      decoration: InputDecoration(
                        hintText: "000000",
                        hintStyle: GoogleFonts.orbitron(color: Colors.white12, fontSize: 24),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(vertical: 20),
                      ),
                    ),
                  ),

                  const SizedBox(height: 30),

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
                      onPressed: _isLoading ? null : _verifyCode,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      child: _isLoading 
                        ? const CircularProgressIndicator(color: Colors.white)
                        : Text("VERIFY & CONFIRM", style: GoogleFonts.orbitron(fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                    ),
                  ).animate(onPlay: (controller) => controller.repeat(reverse: true))
                   .shimmer(duration: 3.seconds, color: Colors.white.withOpacity(0.2)),
                  
                  const SizedBox(height: 20),
                  
                  Center(
                    child: TextButton(
                      onPressed: () async {
                        try {
                          await Amplify.Auth.resendSignUpCode(username: widget.email);
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Code Resent!")));
                        } catch (e) {
                          print(e);
                        }
                      },
                      child: Text("Resend Code", style: GoogleFonts.outfit(color: _accentCyan, fontWeight: FontWeight.w600)),
                    ),
                  )
                ].animate(interval: 80.ms).fade(duration: 450.ms).slideY(begin: 0.08, end: 0, curve: Curves.easeOutQuad),
              ),
            ),
          ),
        ],
      ),
    );
  }
}