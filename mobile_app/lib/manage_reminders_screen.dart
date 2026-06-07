import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:amplify_api/amplify_api.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'models/ModelProvider.dart';
import 'add_reminder_screen.dart';
import 'edit_reminder_screen.dart';

class ManageRemindersScreen extends StatefulWidget {
  const ManageRemindersScreen({super.key});

  @override
  State<ManageRemindersScreen> createState() => _ManageRemindersScreenState();
}

class _ManageRemindersScreenState extends State<ManageRemindersScreen> {
  final Color _accentCyan = const Color(0xFF00F0FF);
  final Color _accentPurple = const Color(0xFF9E00FF);
  final Color _accentPink = const Color(0xFFFF007A);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);
  
  List<Reminder> _reminders = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadReminders();
  }

  Future<void> _loadReminders() async {
    setState(() => _isLoading = true);
    try {
      final request = ModelQueries.list(
        Reminder.classType,
        authorizationMode: APIAuthorizationType.userPools,
      );
      final response = await Amplify.API.query(request: request).response;

      if (response.hasErrors) {
        throw Exception(response.errors.first.message);
      }

      final reminders = response.data?.items.whereType<Reminder>().toList() ?? [];

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

  Future<void> _deleteReminder(Reminder reminder) async {
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
      final request = ModelMutations.delete(
        reminder,
        authorizationMode: APIAuthorizationType.userPools,
      );
      final response = await Amplify.API.mutate(request: request).response;

      if (response.hasErrors) {
        throw Exception(response.errors.first.message);
      }
      
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
         .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.5)),
      ),
      body: Stack(
        children: [
          Positioned(
            top: -50, left: -100,
            child: Container(
              width: 320, height: 320,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentPurple.withOpacity(0.12), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.3, duration: 5.seconds, curve: Curves.easeInOut),
          ),
          SafeArea(
            child: _isLoading 
              ? Center(child: CircularProgressIndicator(color: _accentCyan))
              : _reminders.isEmpty
                  ? Center(
                      child: Text(
                        "No reminders found.\nSchedule a new task!", 
                        textAlign: TextAlign.center,
                        style: GoogleFonts.outfit(color: Colors.white38, fontSize: 15)
                      ).animate().fade().slideY(),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _reminders.length,
                      itemBuilder: (context, index) {
                        return _buildReminderCard(_reminders[index])
                          .animate()
                          .fade(delay: (index * 100).ms)
                          .slideX(begin: 0.15);
                      },
                    ),
          ),
        ],
      ),
      floatingActionButton: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(30),
          gradient: LinearGradient(
            colors: [_accentPurple, _accentCyan],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          boxShadow: [
            BoxShadow(
              color: _accentCyan.withOpacity(0.3),
              blurRadius: 15,
              spreadRadius: 1,
              offset: const Offset(0, 4),
            )
          ],
        ),
        child: FloatingActionButton.extended(
          onPressed: () async {
            await Navigator.push(context, MaterialPageRoute(builder: (context) => const AddReminderScreen()));
            _loadReminders(); 
          },
          backgroundColor: Colors.transparent,
          elevation: 0,
          highlightElevation: 0,
          icon: const Icon(Icons.edit_calendar_rounded, color: Colors.white),
          label: Text("NEW REMINDER", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1)),
        ),
      ).animate(onPlay: (controller) => controller.repeat(reverse: true))
       .shimmer(duration: 3.seconds, color: Colors.white.withOpacity(0.2)),
    );
  }

  Widget _buildReminderCard(Reminder reminder) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _glassWhite,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _glassBorder),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            backgroundColor: _accentPink.withOpacity(0.15),
            child: Icon(Icons.event_note_rounded, color: _accentPink, size: 22),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "📅 ${reminder.date} at ${reminder.time}",
                  style: GoogleFonts.orbitron(color: _accentCyan, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                ),
                const SizedBox(height: 8),
                Text(
                  reminder.reason, 
                  style: GoogleFonts.outfit(color: Colors.white70, fontSize: 14, height: 1.4),
                ),
              ],
            ),
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                icon: Icon(Icons.edit_outlined, color: _accentCyan.withOpacity(0.8)),
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
                icon: const Icon(Icons.delete_outline_rounded, color: Colors.redAccent),
                onPressed: () => _deleteReminder(reminder),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
