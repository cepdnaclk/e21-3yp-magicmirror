import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:amplify_api/amplify_api.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'models/ModelProvider.dart';

class AddFamilyMemberScreen extends StatefulWidget {
  const AddFamilyMemberScreen({super.key});

  @override
  State<AddFamilyMemberScreen> createState() => _AddFamilyMemberScreenState();
}

class _AddFamilyMemberScreenState extends State<AddFamilyMemberScreen> {
  final _nameController = TextEditingController();
  
  // Dropdown State
  final List<String> _relations = ['Father', 'Mother', 'Grandfather', 'Grandmother', 'Guardian'];
  String _selectedRelation = 'Father';

  // Multi-Image State
  final Map<String, Uint8List> _faceAngles = {}; 
  final List<String> _steps = ['front', 'left', 'right'];
  int _currentStepIndex = 0;

  final ImagePicker _picker = ImagePicker();
  bool _isLoading = false;

  final Color _accentCyan = const Color(0xFFFFD86B);
  final Color _accentPurple = const Color(0xFFF6C85F);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);

  Future<void> _pickImage() async {
    if (_currentStepIndex >= _steps.length) return;

    final XFile? returnedImage = await _picker.pickImage(
      source: ImageSource.camera, 
      preferredCameraDevice: CameraDevice.front,
      imageQuality: 70, 
    );

    if (returnedImage != null) {
      final Uint8List bytes = await returnedImage.readAsBytes();
      setState(() {
        _faceAngles[_steps[_currentStepIndex]] = bytes;
        if (_currentStepIndex < _steps.length - 1) {
           _currentStepIndex++;
        }
      });
    }
  }

  Future<void> _saveFamilyMember() async {
    if (_faceAngles.length < 3) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("⚠️ Please provide all 3 angles (Front, Left, Right)!"))
      );
      return;
    }
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("⚠️ Please enter their name!")));
      return;
    }

    setState(() => _isLoading = true);

    try {
      final attributes = await Amplify.Auth.fetchUserAttributes();
      final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
      final mainUserEmail = emailAttr.value.split('@')[0].trim().toLowerCase();
      final cleanName = _nameController.text.trim().replaceAll(' ', '_').toLowerCase();
      final cleanRelation = _selectedRelation.toLowerCase();

      // Loop through and upload each angle
      for (String angle in _faceAngles.keys) {
        final String pathName = 'public/face_entries/${mainUserEmail}_${cleanRelation}_${cleanName}_$angle.jpg';

        await Amplify.Storage.uploadData(
          data: StorageDataPayload.bytes(_faceAngles[angle]!),
          path: StoragePath.fromString(pathName),
        ).result;
      }

      try {
        final newMember = FamilyMember(
          name: _nameController.text.trim(),
          relationship: _selectedRelation,
          imagePaths: [
            'public/face_entries/${mainUserEmail}_${cleanRelation}_${cleanName}_front.jpg',
            'public/face_entries/${mainUserEmail}_${cleanRelation}_${cleanName}_left.jpg',
            'public/face_entries/${mainUserEmail}_${cleanRelation}_${cleanName}_right.jpg'
          ],
        );

        final request = ModelMutations.create(
          newMember,
          authorizationMode: APIAuthorizationType.userPools,
        );
        final response = await Amplify.API.mutate(request: request).response;

        if (response.hasErrors) {
          print('❌ Database Save Error: ${response.errors}');
        } else {
          print('✅ Successfully saved to DynamoDB!');
        }
      } catch (e) {
        print("Failed to save to database: $e");
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("✅ $_selectedRelation registered with AWS Rekognition!"), backgroundColor: Colors.green)
        );
        Navigator.pop(context);
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
    String currentInstruction = _currentStepIndex == 0 ? "Look Straight" : 
                                _currentStepIndex == 1 ? "Turn Left" : "Turn Right";

    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text("ADD FAMILY", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2))
          .animate(onPlay: (controller) => controller.repeat(reverse: true))
          .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.5)),
      ),
      body: Stack(
        children: [
          // Animated Background Gradient 1
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
                  Text("Register Face", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                  Text("Capture 3 angles for better recognition", style: GoogleFonts.outfit(color: Colors.white38, fontSize: 13)),

                  const SizedBox(height: 30),

                  // --- GUIDED CAMERA UI ---
                  Center(
                    child: Column(
                      children: [
                        GestureDetector(
                          onTap: _pickImage,
                          child: Container(
                            height: 150, width: 150,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _glassWhite,
                              border: Border.all(color: _accentCyan.withOpacity(0.3), width: 2),
                              boxShadow: [BoxShadow(color: _accentCyan.withOpacity(0.15), blurRadius: 15)],
                            ),
                            child: _faceAngles[_steps[_currentStepIndex]] != null || (_currentStepIndex == 2 && _faceAngles.containsKey('right'))
                                ? ClipOval(child: Image.memory(_faceAngles[_steps[_currentStepIndex]] ?? _faceAngles['right']!, fit: BoxFit.cover))
                                : Icon(Icons.face_retouching_natural_rounded, color: _accentCyan, size: 45),
                          ).animate(target: _faceAngles.length == 3 ? 1 : 0).shimmer(duration: 1.seconds, color: Colors.white),
                        ),
                        const SizedBox(height: 15),
                        Text(
                          _faceAngles.length == 3 ? "ALL ANGLES CAPTURED" : "STEP: $currentInstruction",
                          style: GoogleFonts.orbitron(color: _accentCyan, fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 1),
                        ).animate(onPlay: (controller) => controller.repeat(reverse: true)).fadeIn().fadeOut(duration: 1.seconds),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 24),

                  // Thumbnail Preview Row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: _steps.map((angle) {
                      bool isCaptured = _faceAngles.containsKey(angle);
                      return Container(
                        margin: const EdgeInsets.symmetric(horizontal: 8),
                        width: 48, height: 48,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: isCaptured ? _accentCyan : Colors.white10),
                          image: isCaptured ? DecorationImage(image: MemoryImage(_faceAngles[angle]!), fit: BoxFit.cover) : null,
                        ),
                        child: !isCaptured ? const Icon(Icons.lock_outline_rounded, color: Colors.white10, size: 18) : null,
                      );
                    }).toList(),
                  ),

                  const SizedBox(height: 30),

                  _buildLabel("Relationship"),
                  _buildDropdown(),

                  const SizedBox(height: 20),

                  _buildLabel("Full Name"),
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
        onPressed: _isLoading ? null : _saveFamilyMember,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        child: _isLoading 
          ? const CircularProgressIndicator(color: Colors.white)
          : Text("AUTHORIZE ACCESS", style: GoogleFonts.orbitron(fontSize: 15, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
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