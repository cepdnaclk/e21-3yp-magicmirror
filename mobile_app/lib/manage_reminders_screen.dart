import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'add_reminder_screen.dart';
import 'edit_reminder_screen.dart';

class ManageRemindersScreen extends StatefulWidget {
  const ManageRemindersScreen({super.key});

  @override
  State<ManageRemindersScreen> createState() => _ManageRemindersScreenState();
}

class _ManageRemindersScreenState extends State<ManageRemindersScreen> {
  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);
  
  List<Map<String, dynamic>> _reminders = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadReminders();
  }

  Future<void> _loadReminders() async {
    setState(() => _isLoading = true);
    try {
      final result = await Amplify.Storage.list(
        path: const StoragePath.fromString('public/reminders/'),
      ).result;

      List<Map<String, dynamic>> reminders = [];
      
      for (var item in result.items) {
        if (item.path.endsWith('/')) continue; 
        
        // Download text file content
        final dataResult = await Amplify.Storage.downloadData(
          path: StoragePath.fromString(item.path)
        ).result;
        
        final text = utf8.decode(dataResult.bytes);

        reminders.add({
          'path': item.path,
          'text': text,
        });
      }

      if (mounted) {
        setState(() {
          _reminders = reminders;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error loading reminders: $e"), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _deleteReminder(String path) async {
    bool confirm = await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: _bgDark,
        title: Text("Delete Reminder?", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Text("Are you sure you want to remove this reminder?", style: GoogleFonts.outfit(color: Colors.white54)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text("CANCEL", style: GoogleFonts.outfit(color: Colors.white54))),
          TextButton(onPressed: () => Navigator.pop(context, true), child: Text("DELETE", style: GoogleFonts.outfit(color: Colors.redAccent, fontWeight: FontWeight.bold))),
        ],
      ),
    ) ?? false;

    if (!confirm) return;

    setState(() => _isLoading = true);
    try {
      await Amplify.Storage.remove(
        path: StoragePath.fromString(path)
      ).result;
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Reminder Deleted!"), backgroundColor: Colors.green));
      }
      await _loadReminders();
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Delete failed: $e"), backgroundColor: Colors.red));
      }
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
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text(
          "MANAGE REMINDERS", 
          style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2)
        ).animate(onPlay: (controller) => controller.repeat(reverse: true))
         .shimmer(duration: 2.seconds, color: _accentColor.withOpacity(0.5)),
      ),
      body: Stack(
        children: [
          Positioned(
            top: -50, left: -100,
            child: Container(
              width: 300, height: 300,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [Colors.cyan.withOpacity(0.1), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.3, duration: 5.seconds, curve: Curves.easeInOut),
          ),
          SafeArea(
            child: _isLoading 
              ? Center(child: CircularProgressIndicator(color: _accentColor))
              : _reminders.isEmpty
                  ? Center(
                      child: Text(
                        "No reminders found.\nSchedule a new task!", 
                        textAlign: TextAlign.center,
                        style: GoogleFonts.outfit(color: Colors.white54, fontSize: 16)
                      ).animate().fade().slideY(),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _reminders.length,
                      itemBuilder: (context, index) {
                        return _buildReminderCard(_reminders[index])
                          .animate()
                          .fade(delay: (index * 100).ms)
                          .slideX(begin: 0.2);
                      },
                    ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.push(context, MaterialPageRoute(builder: (context) => const AddReminderScreen()));
          _loadReminders(); // Reload after coming back
        },
        backgroundColor: _accentColor,
        icon: const Icon(Icons.edit_calendar, color: Colors.black),
        label: Text("NEW REMINDER", style: GoogleFonts.orbitron(color: Colors.black, fontWeight: FontWeight.bold)),
      ).animate(onPlay: (controller) => controller.repeat(reverse: true))
       .boxShadow(
         begin: BoxShadow(color: _accentColor.withOpacity(0.2), blurRadius: 5, spreadRadius: 0),
         end: BoxShadow(color: _accentColor.withOpacity(0.6), blurRadius: 15, spreadRadius: 2),
         duration: 2.seconds,
       ),
    );
  }

  Widget _buildReminderCard(Map<String, dynamic> reminder) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.event_note, color: _accentColor, size: 28),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              reminder['text'], 
              style: GoogleFonts.outfit(color: Colors.white, fontSize: 15, height: 1.4),
            ),
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                icon: const Icon(Icons.edit_outlined, color: Colors.blueAccent),
                onPressed: () async {
                  final result = await Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => EditReminderScreen(reminder: reminder)),
                  );
                  if (result == true) {
                    _loadReminders();
                  }
                },
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                onPressed: () => _deleteReminder(reminder['path']),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
