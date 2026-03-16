import 'dart:typed_data';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class SlideshowScreen extends StatefulWidget {
  const SlideshowScreen({super.key});

  @override
  State<SlideshowScreen> createState() => _SlideshowScreenState();
}

class _SlideshowScreenState extends State<SlideshowScreen> {
  final supabase = Supabase.instance.client;
  final ImagePicker _picker = ImagePicker();
  
  List<Map<String, dynamic>> _photos = [];
  bool _isLoading = true;
  bool _isUploading = false;

  // Theme Colors
  final Color _accentColor = const Color(0xFFC4D300); // Neon Gold
  final Color _bgDark = const Color(0xFF0A0B10);

  @override
  void initState() {
    super.initState();
    _fetchPhotos();
  }

  // --- FETCH PHOTOS FROM DATABASE ---
  Future<void> _fetchPhotos() async {
    try {
      final data = await supabase.from('slideshow').select().order('created_at', ascending: false);
      setState(() {
        _photos = data;
        _isLoading = false;
      });
    } catch (e) {
      print("Error fetching photos: $e");
      setState(() => _isLoading = false);
    }
  }

  // --- UPLOAD NEW PHOTO ---
  Future<void> _uploadPhoto() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 70);
    
    if (image == null) return;

    setState(() => _isUploading = true);

    try {
      final Uint8List bytes = await image.readAsBytes();
      final String fileName = '${DateTime.now().millisecondsSinceEpoch}.jpg';

      // 1. Upload to Storage
      await supabase.storage.from('slideshow').uploadBinary(fileName, bytes);

      // 2. Get URL
      final String imageUrl = supabase.storage.from('slideshow').getPublicUrl(fileName);

      // 3. Save to Database
      await supabase.from('slideshow').insert({'image_url': imageUrl});

      // 4. Refresh the Grid
      _fetchPhotos();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Photo added to Mirror Slideshow!"), backgroundColor: Colors.green)
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Upload Error: $e"), backgroundColor: Colors.red)
        );
      }
    } finally {
      if (mounted) setState(() => _isUploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text("MIRROR GALLERY", 
          style: GoogleFonts.orbitron(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: 2)
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(color: Colors.black.withOpacity(0.2)),
          ),
        ),
      ),
      
      // Upload Button
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: _accentColor,
        onPressed: _isUploading ? null : _uploadPhoto,
        icon: _isUploading 
          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2))
          : const Icon(Icons.add_photo_alternate, color: Colors.black),
        label: Text("ADD PHOTO", style: GoogleFonts.orbitron(color: Colors.black, fontWeight: FontWeight.bold)),
      ),

      body: Stack(
        children: [
          // Background Glow
          Positioned(
            top: 100,
            left: -50,
            child: Container(
              width: 300, height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(colors: [_accentColor.withOpacity(0.1), Colors.transparent]),
              ),
            ),
          ),

          // Main Content
          SafeArea(
            child: _isLoading 
              ? Center(child: CircularProgressIndicator(color: _accentColor))
              : _photos.isEmpty
                  ? Center(child: Text("No photos yet. Add some!", style: GoogleFonts.outfit(color: Colors.white54)))
                  : GridView.builder(
                      padding: const EdgeInsets.all(16),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2, // 2 photos per row
                        crossAxisSpacing: 16,
                        mainAxisSpacing: 16,
                        childAspectRatio: 1, // Square crop
                      ),
                      itemCount: _photos.length,
                      itemBuilder: (context, index) {
                        final photoUrl = _photos[index]['image_url'];
                        return ClipRRect(
                          borderRadius: BorderRadius.circular(16),
                          child: Container(
                            decoration: BoxDecoration(
                              border: Border.all(color: Colors.white.withOpacity(0.1)),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Image.network(
                              photoUrl,
                              fit: BoxFit.cover,
                              loadingBuilder: (context, child, progress) {
                                if (progress == null) return child;
                                return Center(child: CircularProgressIndicator(color: _accentColor));
                              },
                            ),
                          ),
                        );
                      },
                    ),
          ),
        ],
      ),
    );
  }
}