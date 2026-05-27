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

  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);

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
          .shimmer(duration: 2.seconds, color: _accentColor.withOpacity(0.5)), 
        iconTheme: const IconThemeData(color: Colors.white)
      ),
      body: Stack(
        children: [
          Positioned(
            top: -100, left: -100,
            child: Container(
              width: 400, height: 400,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentColor.withOpacity(0.15), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.2, duration: 4.seconds, curve: Curves.easeInOut)
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
                  _glassTextField(_textController, "Enter reminder text...", Icons.edit_note, maxLines: 5),
                  const SizedBox(height: 40),
                  SizedBox(
                    width: double.infinity, height: 55, 
                    child: ElevatedButton(
                      onPressed: _isSaving ? null : _updateReminder, 
                      style: ElevatedButton.styleFrom(backgroundColor: _accentColor, foregroundColor: Colors.black, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))), 
                      child: _isSaving ? const CircularProgressIndicator(color: Colors.black) : Text("SAVE CHANGES", style: GoogleFonts.orbitron(fontSize: 16, fontWeight: FontWeight.bold))
                    )
                  ).animate(onPlay: (controller) => controller.repeat(reverse: true))
                   .boxShadow(
                     begin: BoxShadow(color: _accentColor.withOpacity(0.2), blurRadius: 5, spreadRadius: 0),
                     end: BoxShadow(color: _accentColor.withOpacity(0.6), blurRadius: 15, spreadRadius: 2),
                     duration: 2.seconds,
                   ),
                ].animate(interval: 100.ms).fade(duration: 500.ms).slideY(begin: 0.1, end: 0, curve: Curves.easeOutQuad),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String text) => Text(text, style: GoogleFonts.orbitron(color: Colors.white54, fontSize: 12, letterSpacing: 2, fontWeight: FontWeight.bold));
  
  Widget _glassTextField(TextEditingController controller, String hint, IconData icon, {int maxLines = 1}) => Container(
    decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.white.withOpacity(0.1))), 
    child: TextField(controller: controller, maxLines: maxLines, style: GoogleFonts.outfit(color: Colors.white, height: 1.5), decoration: InputDecoration(hintText: hint, hintStyle: GoogleFonts.outfit(color: Colors.white38), border: InputBorder.none, contentPadding: const EdgeInsets.all(18)))
  );
}
