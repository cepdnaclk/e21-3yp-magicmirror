import 'dart:typed_data'; // <--- NEW: For Web Support
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter/services.dart';
import 'database_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final DatabaseService _db = DatabaseService();
  
  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _pinCtrl = TextEditingController();

  String _selectedRole = 'Family'; 
  final List<String> _roles = ['Admin', 'Family', 'Guest'];

  String _selectedTheme = 'Shrek';
  final List<String> _themes = ['Shrek', 'Cyberpunk', 'Minimalist'];

  // CHANGED: We now store the photo as "Bytes", not a "File"
  Uint8List? _photoBytes; 
  bool _isLoading = false;

  Future<void> _takePhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera, preferredCameraDevice: CameraDevice.front);
    
    if (picked != null) {
      // Read the file as bytes (Web Compatible)
      final bytes = await picked.readAsBytes();
      setState(() => _photoBytes = bytes);
    }
  }

  Future<void> _submit() async {
    if (_photoBytes == null || _nameCtrl.text.isEmpty || _pinCtrl.text.length != 4) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please fill all fields & 4-digit PIN!")));
      return;
    }
    
    setState(() => _isLoading = true);
    
    try {
      await _db.uploadProfile(
        name: _nameCtrl.text, 
        role: _selectedRole, 
        pin: _pinCtrl.text,       
        theme: _selectedTheme,    
        photoBytes: _photoBytes! // <--- Sending Bytes
      );
      
      if(mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("User Created Successfully!")));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text("Create Profile", style: GoogleFonts.bangers(color: const Color(0xFFC4D300), fontSize: 25)), 
        backgroundColor: Colors.grey[900],
        iconTheme: const IconThemeData(color: Color(0xFFC4D300)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(25),
        child: Column(
          children: [
            // 1. PHOTO
            GestureDetector(
              onTap: _takePhoto,
              child: CircleAvatar(
                radius: 70,
                backgroundColor: Colors.grey[800],
                // CHANGED: Use MemoryImage for bytes
                backgroundImage: _photoBytes != null ? MemoryImage(_photoBytes!) : null,
                child: _photoBytes == null ? const Icon(Icons.camera_alt, size: 40, color: Color(0xFFC4D300)) : null,
              ),
            ),
            const SizedBox(height: 10),
            const Text("Tap for Selfie", style: TextStyle(color: Colors.grey)),

            const SizedBox(height: 30),

            // 2. NAME
            _buildTextField(label: "Name (e.g. Donkey)", controller: _nameCtrl, icon: Icons.person),
            
            const SizedBox(height: 20),

            // 3. PIN CODE
            _buildTextField(
              label: "4-Digit PIN (Backup Access)", 
              controller: _pinCtrl, 
              icon: Icons.lock, 
              isNumber: true
            ),

            const SizedBox(height: 20),

            // 4. DROPDOWNS
            Row(
              children: [
                Expanded(child: _buildDropdown("Role", _selectedRole, _roles, (val) => setState(() => _selectedRole = val!))),
                const SizedBox(width: 15),
                Expanded(child: _buildDropdown("Theme", _selectedTheme, _themes, (val) => setState(() => _selectedTheme = val!))),
              ],
            ),

            const SizedBox(height: 50),

            // 5. REGISTER BUTTON
            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFC4D300)),
                onPressed: _isLoading ? null : _submit,
                child: _isLoading 
                  ? const CircularProgressIndicator(color: Colors.black) 
                  : const Text("REGISTER USER", style: TextStyle(color: Colors.black, fontSize: 18, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // --- Helpers ---
  Widget _buildTextField({required String label, required TextEditingController controller, required IconData icon, bool isNumber = false}) {
    return TextField(
      controller: controller,
      keyboardType: isNumber ? TextInputType.number : TextInputType.text,
      maxLength: isNumber ? 4 : null,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Colors.grey),
        prefixIcon: Icon(icon, color: const Color(0xFFC4D300)),
        enabledBorder: OutlineInputBorder(borderSide: const BorderSide(color: Colors.grey), borderRadius: BorderRadius.circular(10)),
        focusedBorder: OutlineInputBorder(borderSide: const BorderSide(color: Color(0xFFC4D300)), borderRadius: BorderRadius.circular(10)),
        filled: true,
        fillColor: Colors.grey[900],
        counterText: "",
      ),
    );
  }

  Widget _buildDropdown(String title, String value, List<String> items, Function(String?) onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 5),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          decoration: BoxDecoration(color: Colors.grey[900], borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.grey)),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: value,
              dropdownColor: Colors.grey[900],
              isExpanded: true,
              icon: const Icon(Icons.arrow_drop_down, color: Color(0xFFC4D300)),
              items: items.map((e) => DropdownMenuItem(value: e, child: Text(e, style: const TextStyle(color: Colors.white)))).toList(),
              onChanged: onChanged,
            ),
          ),
        ),
      ],
    );
  }
}