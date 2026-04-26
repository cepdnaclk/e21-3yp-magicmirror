import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:amplify_flutter/amplify_flutter.dart';

class SlideshowScreen extends StatefulWidget {
  const SlideshowScreen({super.key});

  @override
  State<SlideshowScreen> createState() => _SlideshowScreenState();
}

class _SlideshowScreenState extends State<SlideshowScreen> {
  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);
  
  List<String> _imageUrls = [];
  bool _isLoading = true;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadImages();
  }

  // --- 1. FETCH IMAGES FROM AWS S3 ---
  Future<void> _loadImages() async {
    setState(() => _isLoading = true);
    try {
      // Get the list of files in the slideshow folder
      final result = await Amplify.Storage.list(
        path: StoragePath.fromString('public/slideshow/'),
      ).result;

      List<String> urls = [];
      
      // Convert those files into temporary viewing URLs
      for (var item in result.items) {
        // Skip the folder itself if it returns as an item
        if (item.path.endsWith('/')) continue; 
        
        final urlResult = await Amplify.Storage.getUrl(
          path: StoragePath.fromString(item.path)
        ).result;
        urls.add(urlResult.url.toString());
      }

      if (mounted) {
        setState(() {
          _imageUrls = urls;
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

  // --- 2. UPLOAD NEW IMAGE TO AWS S3 ---
  Future<void> _uploadImage() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image == null) return;

    setState(() => _isLoading = true);
    try {
      final Uint8List bytes = await image.readAsBytes();
      // Create a unique filename using a timestamp
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
      
      // Refresh the gallery to show the new image
      await _loadImages();
      
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Upload failed: $e"), backgroundColor: Colors.red));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text(
          "MANAGE SLIDESHOW", 
          style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2)
        ),
      ),
      body: _isLoading 
        ? Center(child: CircularProgressIndicator(color: _accentColor))
        : _imageUrls.isEmpty
            ? Center(
                child: Text(
                  "No images found.\nUpload a photo to display on the mirror!", 
                  textAlign: TextAlign.center,
                  style: GoogleFonts.outfit(color: Colors.white54, fontSize: 16)
                ),
              )
            : GridView.builder(
                padding: const EdgeInsets.all(16),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2, // 2 images per row
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  childAspectRatio: 1, // Square images
                ),
                itemCount: _imageUrls.length,
                itemBuilder: (context, index) {
                  return _buildImageCard(_imageUrls[index]);
                },
              ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _uploadImage,
        backgroundColor: _accentColor,
        icon: const Icon(Icons.add_photo_alternate, color: Colors.black),
        label: Text("ADD PHOTO", style: GoogleFonts.orbitron(color: Colors.black, fontWeight: FontWeight.bold)),
      ),
    );
  }

  // FIXED: Chrome-safe image container
  Widget _buildImageCard(String imageUrl) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(15),
        child: Image.network(
          imageUrl,
          fit: BoxFit.cover,
          loadingBuilder: (context, child, loadingProgress) {
            if (loadingProgress == null) return child;
            return Center(
              child: CircularProgressIndicator(
                color: _accentColor,
                value: loadingProgress.expectedTotalBytes != null
                    ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                    : null,
              ),
            );
          },
          errorBuilder: (context, error, stackTrace) {
            return const Center(child: Icon(Icons.broken_image, color: Colors.white24, size: 40));
          },
        ),
      ),
    );
  }
}