import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:amplify_api/amplify_api.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'models/ModelProvider.dart';

class EditReminderScreen extends StatefulWidget {
  final Reminder reminder;

  const EditReminderScreen({super.key, required this.reminder});

  @override
  State<EditReminderScreen> createState() => _EditReminderScreenState();
}

class _EditReminderScreenState extends State<EditReminderScreen> {
  late TextEditingController _textController;
  bool _isSaving = false;

  final Color _accentCyan = const Color(0xFFFFD86B);
  final Color _accentPurple = const Color(0xFFF6C85F);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(text: widget.reminder.reason);
  }

  Future<void> _updateReminder() async {
    if (_textController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Text cannot be empty!"), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isSaving = true);

    try {
      final updatedReminder = widget.reminder.copyWith(
        reason: _textController.text.trim()
      );

      final request = ModelMutations.update(
        updatedReminder,
        authorizationMode: APIAuthorizationType.userPools,
      );
      final response = await Amplify.API.mutate(request: request).response;

      if (response.hasErrors) {
        throw Exception(response.errors.first.message);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Reminder updated!"), backgroundColor: Colors.green));
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red));
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent, 
        elevation: 0, 
        title: Text("EDIT REMINDER", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2))
          .animate(onPlay: (controller) => controller.repeat(reverse: true))
          .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.5)), 
        iconTheme: const IconThemeData(color: Colors.white)
      ),
      body: Stack(
        children: [
          Positioned(
            top: -100, left: -100,
            child: Container(
              width: 400, height: 400,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentPurple.withOpacity(0.12), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.25, duration: 4.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds),
          ),
          
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _sectionTitle("REMINDER TEXT"),
                  const SizedBox(height: 10),
                  _glassTextField(_textController, "Enter reminder text...", Icons.edit_note_rounded, maxLines: 5),
                  const SizedBox(height: 40),
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
                      onPressed: _isSaving ? null : _updateReminder, 
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent, 
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white, 
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))
                      ), 
                      child: _isSaving 
                        ? const CircularProgressIndicator(color: Colors.white) 
                        : Text("SAVE CHANGES", style: GoogleFonts.orbitron(fontSize: 15, fontWeight: FontWeight.bold, letterSpacing: 1.5))
                    )
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

  Widget _sectionTitle(String text) => Text(text, style: GoogleFonts.orbitron(color: Colors.white70, fontSize: 11, letterSpacing: 1.5, fontWeight: FontWeight.bold));
  
  Widget _glassTextField(TextEditingController controller, String hint, IconData icon, {int maxLines = 1}) => Container(
    decoration: BoxDecoration(color: _glassWhite, borderRadius: BorderRadius.circular(16), border: Border.all(color: _glassBorder)), 
    child: TextField(
      controller: controller, 
      maxLines: maxLines, 
      style: GoogleFonts.outfit(color: Colors.white, height: 1.5, fontSize: 15), 
      decoration: InputDecoration(
        hintText: hint, 
        hintStyle: GoogleFonts.outfit(color: Colors.white24, fontSize: 14), 
        border: InputBorder.none, 
        contentPadding: const EdgeInsets.all(16)
      )
    )
  );
}
