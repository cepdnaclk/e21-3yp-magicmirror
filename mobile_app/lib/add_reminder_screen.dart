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

  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);

  Future<void> _sendReminder() async {
    if (_reasonController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please enter a reason!"), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isSending = true);

    try {
      String dateStr = _selectedDate != null ? "${_selectedDate!.month}/${_selectedDate!.day}/${_selectedDate!.year}" : "Today";
      String timeStr = _selectedTime != null ? _selectedTime!.format(context) : "Anytime";
      
      // Create a new Reminder model instance
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
                  _sectionTitle("DATE & TIME"),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(child: _glassButton(_selectedDate == null ? "Select Date" : "${_selectedDate!.month}/${_selectedDate!.day}/${_selectedDate!.year}", Icons.calendar_month, () => _pickDate())), 
                      const SizedBox(width: 15), 
                      Expanded(child: _glassButton(_selectedTime == null ? "Select Time" : _selectedTime!.format(context), Icons.access_time, () => _pickTime()))
                    ]
                  ),
                  const SizedBox(height: 30),
                  _sectionTitle("REASON"),
                  const SizedBox(height: 10),
                  _glassTextField(_reasonController, "e.g. Lab Session, Submit Project...", Icons.edit_note, maxLines: 3),
                  const SizedBox(height: 40),
                  SizedBox(
                    width: double.infinity, height: 55, 
                    child: ElevatedButton(
                      onPressed: _isSending ? null : _sendReminder, 
                      style: ElevatedButton.styleFrom(backgroundColor: _accentColor, foregroundColor: Colors.black, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))), 
                      child: _isSending ? const CircularProgressIndicator(color: Colors.black) : Text("SEND TO SCHEDULE", style: GoogleFonts.orbitron(fontSize: 16, fontWeight: FontWeight.bold))
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
    child: TextField(controller: controller, maxLines: maxLines, style: GoogleFonts.outfit(color: Colors.white), decoration: InputDecoration(hintText: hint, hintStyle: GoogleFonts.outfit(color: Colors.white38), border: InputBorder.none, contentPadding: const EdgeInsets.all(18)))
  );
  
  Widget _glassButton(String label, IconData icon, VoidCallback onTap) => Material(
    color: Colors.transparent,
    child: InkWell(
      onTap: onTap, 
      borderRadius: BorderRadius.circular(15), 
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 18), 
        decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(15), border: Border.all(color: Colors.white.withOpacity(0.1))), 
        child: Column(
          children: [
            Icon(icon, color: _accentColor, size: 24), 
            const SizedBox(height: 8), 
            Text(label, style: GoogleFonts.outfit(color: Colors.white, fontSize: 14))
          ]
        )
      )
    ),
  );
}