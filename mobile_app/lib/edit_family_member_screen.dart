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

  final Color _accentCyan = const Color(0xFFFFD86B);
  final Color _accentPurple = const Color(0xFFF6C85F);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

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

      final request = ModelMutations.update(
        updatedMember,
        authorizationMode: APIAuthorizationType.userPools,
      );
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
          .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.5)),
      ),
      body: Stack(
        children: [
          Positioned(
            top: -50, right: -100,
            child: Container(
              width: 350, height: 350,
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
                  Text("Update Details", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                  const SizedBox(height: 30),

                  _buildLabel("Relationship"),
                  _buildDropdown(),
                  const SizedBox(height: 20),

                  _buildLabel("First Name"),
                  _buildTextField(),
                  const SizedBox(height: 40),

                  _buildSaveButton(),
                ].animate(interval: 80.ms).fade(duration: 450.ms).slideY(begin: 0.08, end: 0, curve: Curves.easeOutQuad),
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
        color: Colors.white.withOpacity(0.03), 
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _glassBorder),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: _selectedRelation,
          dropdownColor: _bgDark,
          isExpanded: true,
          style: GoogleFonts.outfit(color: Colors.white, fontSize: 15),
          items: _relations.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
          onChanged: (val) => setState(() => _selectedRelation = val!),
        ),
      ),
    );
  }

  Widget _buildTextField() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03), 
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _glassBorder),
      ),
      child: TextField(
        controller: _nameController,
        style: GoogleFonts.outfit(color: Colors.white, fontSize: 15),
        decoration: InputDecoration(
          hintText: "Enter their name",
          hintStyle: GoogleFonts.outfit(color: Colors.white24, fontSize: 14),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          border: InputBorder.none,
        ),
      ),
    );
  }

  Widget _buildSaveButton() {
    return Container(
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
        onPressed: _isLoading ? null : _updateFamilyMember,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        child: _isLoading 
          ? const CircularProgressIndicator(color: Colors.white)
          : Text("SAVE CHANGES", style: GoogleFonts.orbitron(fontSize: 15, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
      ),
    ).animate(onPlay: (controller) => controller.repeat(reverse: true))
     .shimmer(duration: 3.seconds, color: Colors.white.withOpacity(0.2));
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0, left: 5),
      child: Text(text, style: GoogleFonts.orbitron(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1)),
    );
  }
}
