import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:flutter_animate/flutter_animate.dart';

class SlideshowScreen extends StatefulWidget {
  const SlideshowScreen({super.key});

  @override
  State<SlideshowScreen> createState() => _SlideshowScreenState();
}

class _SlideshowScreenState extends State<SlideshowScreen> {
  final Color _accentCyan = const Color(0xFF00F0FF);
  final Color _accentPurple = const Color(0xFF9E00FF);
  final Color _bgDark = const Color(0xFF07080E);
  final Color _glassWhite = Colors.white.withOpacity(0.03);
  final Color _glassBorder = Colors.white.withOpacity(0.06);
  
  List<Map<String, String>> _images = [];
  bool _isLoading = true;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadImages();
  }

  Future<void> _loadImages() async {
    setState(() => _isLoading = true);
    try {
      final result = await Amplify.Storage.list(
        path: StoragePath.fromString('public/slideshow/'),
      ).result;

      List<Map<String, String>> images = [];
      
      for (var item in result.items) {
        if (item.path.endsWith('/')) continue; 
        
        final urlResult = await Amplify.Storage.getUrl(
          path: StoragePath.fromString(item.path)
        ).result;
        
        images.add({
          'path': item.path,
          'url': urlResult.url.toString(),
        });
      }

      if (mounted) {
        setState(() {
          _images = images;
          _isLoading = false;
        });
      }
    } catch (e) {
      print("Error loading images: $e");
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error loading images: $e"), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _uploadImage() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image == null) return;

    setState(() => _isLoading = true);
    try {
      final Uint8List bytes = await image.readAsBytes();
      final String fileName = 'slide_${DateTime.now().millisecondsSinceEpoch}.jpg';

      await Amplify.Storage.uploadData(
        data: StorageDataPayload.bytes(bytes),
        path: StoragePath.fromString('public/slideshow/$fileName'),
      ).result;

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("✅ Image Added to Mirror!"), backgroundColor: Colors.green)
        );
      }
      
      await _loadImages();
      
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Upload failed: $e"), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _deleteImage(String path) async {
    bool confirm = await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: _bgDark,
        title: Text("Delete Photo?", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Text("Are you sure you want to remove this photo from the mirror?", style: GoogleFonts.outfit(color: Colors.white54)),
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
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Image Deleted!"), backgroundColor: Colors.green));
      }
      await _loadImages();
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
          "MANAGE SLIDESHOW", 
          style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2)
        ).animate(onPlay: (controller) => controller.repeat(reverse: true))
         .shimmer(duration: 3.seconds, color: _accentCyan.withOpacity(0.5)),
      ),
      body: Stack(
        children: [
          Positioned(
            bottom: -50, left: -100,
            child: Container(
              width: 320, height: 320,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentPurple.withOpacity(0.12), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.3, duration: 5.seconds, curve: Curves.easeInOut)
             .fadeIn(duration: 2.seconds),
          ),
          
          SafeArea(
            child: _isLoading 
              ? Center(child: CircularProgressIndicator(color: _accentCyan))
              : _images.isEmpty
                  ? Center(
                      child: Text(
                        "No images found.\nUpload a photo to display on the mirror!", 
                        textAlign: TextAlign.center,
                        style: GoogleFonts.outfit(color: Colors.white38, fontSize: 15)
                      ).animate().fade().slideY(),
                    )
                  : GridView.builder(
                      padding: const EdgeInsets.all(16),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2, 
                        crossAxisSpacing: 16,
                        mainAxisSpacing: 16,
                        childAspectRatio: 1, 
                      ),
                      itemCount: _images.length,
                      itemBuilder: (context, index) {
                        return _buildImageCard(_images[index])
                          .animate()
                          .fade(delay: (index * 100).ms)
                          .scale(delay: (index * 100).ms);
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
          onPressed: _uploadImage,
          backgroundColor: Colors.transparent,
          elevation: 0,
          highlightElevation: 0,
          icon: const Icon(Icons.add_photo_alternate_rounded, color: Colors.white),
          label: Text("ADD PHOTO", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1)),
        ),
      ).animate(onPlay: (controller) => controller.repeat(reverse: true))
       .shimmer(duration: 3.seconds, color: Colors.white.withOpacity(0.2)),
    );
  }

  Widget _buildImageCard(Map<String, String> imageData) {
    return Stack(
      fit: StackFit.expand,
      children: [
        Container(
          decoration: BoxDecoration(
            color: _glassWhite,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: _glassBorder),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(19),
            child: Image.network(
              imageData['url']!,
              fit: BoxFit.cover,
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;
                return Center(
                  child: CircularProgressIndicator(
                    color: _accentCyan,
                    value: loadingProgress.expectedTotalBytes != null
                        ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                        : null,
                  ),
                );
              },
              errorBuilder: (context, error, stackTrace) {
                return const Center(child: Icon(Icons.broken_image_rounded, color: Colors.white24, size: 36));
              },
            ),
          ),
        ),
        Positioned(
          top: 8,
          right: 8,
          child: GestureDetector(
            onTap: () => _deleteImage(imageData['path']!),
            child: Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.6),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.redAccent.withOpacity(0.3)),
              ),
              child: const Icon(Icons.delete_outline_rounded, color: Colors.redAccent, size: 18),
            ),
          ),
        ),
      ],
    );
  }
}