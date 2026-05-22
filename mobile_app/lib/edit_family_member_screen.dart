import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:amplify_api/amplify_api.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'models/ModelProvider.dart';

class EditFamilyMemberScreen extends StatefulWidget {
  final FamilyMember member;

  const EditFamilyMemberScreen({super.key, required this.member});

  @override
  State<EditFamilyMemberScreen> createState() => _EditFamilyMemberScreenState();
}

class _EditFamilyMemberScreenState extends State<EditFamilyMemberScreen> {
  late TextEditingController _nameController;
  
  final List<String> _relations = ['Father', 'Mother', 'Grandfather', 'Grandmother', 'Guardian', 'Son', 'Daughter', 'Brother', 'Sister'];
  late String _selectedRelation;

  bool _isLoading = false;

  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.member.name);
    _selectedRelation = _relations.contains(widget.member.relationship) 
        ? widget.member.relationship 
        : _relations.first;
  }

  Future<void> _updateFamilyMember() async {
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("⚠️ Please enter a name!")));
      return;
    }

    setState(() => _isLoading = true);

    try {
      final updatedMember = widget.member.copyWith(
        name: _nameController.text.trim(),
        relationship: _selectedRelation,
      );

      final request = ModelMutations.update(updatedMember);
      final response = await Amplify.API.mutate(request: request).response;

      if (response.hasErrors) {
        print('❌ Database Update Error: ${response.errors}');
        throw Exception("Failed to update member.");
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("✅ Member updated successfully!"), backgroundColor: Colors.green)
        );
        Navigator.pop(context, true); // Return true to indicate success
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
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
        title: Text("EDIT MEMBER", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2))
          .animate(onPlay: (controller) => controller.repeat(reverse: true))
          .shimmer(duration: 2.seconds, color: _accentColor.withOpacity(0.5)),
      ),
      body: Stack(
        children: [
          Positioned(
            top: -50, right: -100,
            child: Container(
              width: 350, height: 350,
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
                  Text("Update Details", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 30),

                  _buildLabel("Relationship"),
                  _buildDropdown(),
                  const SizedBox(height: 20),

                  _buildLabel("First Name"),
                  _buildTextField(),
                  const SizedBox(height: 40),

                  _buildSaveButton(),
                ].animate(interval: 100.ms).fade(duration: 500.ms).slideY(begin: 0.1, end: 0, curve: Curves.easeOutQuad),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDropdown() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.08), 
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: _selectedRelation,
          dropdownColor: _bgDark,
          isExpanded: true,
          style: GoogleFonts.outfit(color: Colors.white, fontSize: 16),
          items: _relations.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
          onChanged: (val) => setState(() => _selectedRelation = val!),
        ),
      ),
    );
  }

  Widget _buildTextField() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.08), 
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: TextField(
        controller: _nameController,
        style: GoogleFonts.outfit(color: Colors.white),
        decoration: InputDecoration(
          hintText: "Enter their name",
          hintStyle: GoogleFonts.outfit(color: Colors.white24),
          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
          border: InputBorder.none,
        ),
      ),
    );
  }

  Widget _buildSaveButton() {
    return SizedBox(
      width: double.infinity, height: 55,
      child: ElevatedButton(
        onPressed: _isLoading ? null : _updateFamilyMember,
        style: ElevatedButton.styleFrom(
          backgroundColor: _accentColor,
          foregroundColor: Colors.black,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        ),
        child: _isLoading 
          ? const CircularProgressIndicator(color: Colors.black)
          : Text("SAVE CHANGES", style: GoogleFonts.orbitron(fontSize: 16, fontWeight: FontWeight.bold)),
      ),
    ).animate(onPlay: (controller) => controller.repeat(reverse: true))
     .boxShadow(
       begin: BoxShadow(color: _accentColor.withOpacity(0.2), blurRadius: 5, spreadRadius: 0),
       end: BoxShadow(color: _accentColor.withOpacity(0.6), blurRadius: 15, spreadRadius: 2),
       duration: 2.seconds,
     );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0, left: 5),
      child: Text(text, style: GoogleFonts.orbitron(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }
}
