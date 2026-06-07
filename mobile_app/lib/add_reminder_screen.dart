import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:amplify_api/amplify_api.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'models/ModelProvider.dart';

class AddReminderScreen extends StatefulWidget {
  const AddReminderScreen({super.key});

  @override
  State<AddReminderScreen> createState() => _AddReminderScreenState();
}

class _AddReminderScreenState extends State<AddReminderScreen> {
  final TextEditingController _reasonController = TextEditingController();
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;
  bool _isSending = false;

  final Color _accentCyan = const Color(0xFF00F0FF);
  final Color _accentPurple = const Color(0xFF9E00FF);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

  Future<void> _sendReminder() async {
    if (_reasonController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please enter a reason!"), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isSending = true);

    try {
      String dateStr = _selectedDate != null ? "${_selectedDate!.month}/${_selectedDate!.day}/${_selectedDate!.year}" : "Today";
      String timeStr = _selectedTime != null ? _selectedTime!.format(context) : "Anytime";
      
      // 1. Create a new Reminder model instance and save to DynamoDB
      final newReminder = Reminder(
        date: dateStr,
        time: timeStr,
        reason: _reasonController.text.trim(),
      );

      // Save to DynamoDB via Amplify API
      final request = ModelMutations.create(
        newReminder,
        authorizationMode: APIAuthorizationType.userPools,
      );
      final response = await Amplify.API.mutate(request: request).response;

      if (response.hasErrors) {
        throw Exception(response.errors.first.message);
      }

      // 2. Dual-write: Upload the reminder file to the S3 bucket (under public/reminders/)
      try {
        final attributes = await Amplify.Auth.fetchUserAttributes();
        final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
        final userPrefix = emailAttr.value.replaceAll('@gmail.com', '').toLowerCase().trim();

        String finalMessage = "📅 Upcoming: $dateStr at $timeStr\n👉 ${_reasonController.text.trim()}";
        final String timestamp = DateTime.now().millisecondsSinceEpoch.toString();
        final String pathName = 'public/reminders/${userPrefix}_Task_$timestamp.txt';

        await Amplify.Storage.uploadData(
          data: StorageDataPayload.string(finalMessage),
          path: StoragePath.fromString(pathName),
        ).result;
      } catch (s3Error) {
        // Log S3 error but don't fail the operation since the database save succeeded
        print("S3 Upload failed: $s3Error");
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Task added to Priority Schedule!"), backgroundColor: Colors.green));
        Navigator.pop(context); 
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red));
    } finally {
      if (mounted) setState(() => _isSending = false);
    }
  }

  Future<void> _pickDate() async {
    DateTime? picked = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime.now(), lastDate: DateTime(2030));
    if (picked != null) setState(() => _selectedDate = picked);
  }

  Future<void> _pickTime() async {
    TimeOfDay? picked = await showTimePicker(context: context, initialTime: TimeOfDay.now());
    if (picked != null) setState(() => _selectedTime = picked);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent, 
        elevation: 0, 
        title: Text("NEW REMINDER", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2))
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
                  _sectionTitle("DATE & TIME"),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(child: _glassButton(_selectedDate == null ? "Select Date" : "${_selectedDate!.month}/${_selectedDate!.day}/${_selectedDate!.year}", Icons.calendar_month_rounded, () => _pickDate())), 
                      const SizedBox(width: 15), 
                      Expanded(child: _glassButton(_selectedTime == null ? "Select Time" : _selectedTime!.format(context), Icons.access_time_rounded, () => _pickTime()))
                    ]
                  ),
                  const SizedBox(height: 30),
                  _sectionTitle("REASON"),
                  const SizedBox(height: 10),
                  _glassTextField(_reasonController, "e.g. Lab Session, Submit Project...", Icons.edit_note_rounded, maxLines: 3),
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
                      onPressed: _isSending ? null : _sendReminder, 
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent, 
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white, 
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))
                      ), 
                      child: _isSending 
                        ? const CircularProgressIndicator(color: Colors.white) 
                        : Text("SEND TO SCHEDULE", style: GoogleFonts.orbitron(fontSize: 15, fontWeight: FontWeight.bold, letterSpacing: 1.5))
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
      style: GoogleFonts.outfit(color: Colors.white, fontSize: 15), 
      decoration: InputDecoration(
        hintText: hint, 
        hintStyle: GoogleFonts.outfit(color: Colors.white24, fontSize: 14), 
        border: InputBorder.none, 
        contentPadding: const EdgeInsets.all(16)
      )
    )
  );
  
  Widget _glassButton(String label, IconData icon, VoidCallback onTap) => Material(
    color: Colors.transparent,
    child: InkWell(
      onTap: onTap, 
      borderRadius: BorderRadius.circular(16), 
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 18), 
        decoration: BoxDecoration(color: _glassWhite, borderRadius: BorderRadius.circular(16), border: Border.all(color: _glassBorder)), 
        child: Column(
          children: [
            Icon(icon, color: _accentCyan, size: 24), 
            const SizedBox(height: 8), 
            Text(label, style: GoogleFonts.outfit(color: Colors.white, fontSize: 13))
          ]
        )
      )
    ),
  );
}