import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:amplify_api/amplify_api.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'add_family_member_screen.dart';
import 'edit_family_member_screen.dart';
import 'models/ModelProvider.dart';

class ManageFamilyMembersScreen extends StatefulWidget {
  const ManageFamilyMembersScreen({super.key});

  @override
  State<ManageFamilyMembersScreen> createState() => _ManageFamilyMembersScreenState();
}

class _ManageFamilyMembersScreenState extends State<ManageFamilyMembersScreen> {
  final Color _accentColor = const Color(0xFFC4D300);
  final Color _bgDark = const Color(0xFF0A0B10);

  List<FamilyMember> _members = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadMembers();
  }

  Future<void> _loadMembers() async {
    setState(() => _isLoading = true);
    try {
      final request = ModelQueries.list(
        FamilyMember.classType,
        authorizationMode: APIAuthorizationType.userPools,
      );
      final response = await Amplify.API.query(request: request).response;

      final members = response.data?.items.whereType<FamilyMember>().toList() ?? [];
      
      if (mounted) {
        setState(() {
          _members = members;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error loading family members: $e"), backgroundColor: Colors.red)
        );
      }
    }
  }

  Future<void> _deleteMember(FamilyMember member) async {
    bool confirm = await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: _bgDark,
        title: Text("Delete Member?", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Text("Are you sure you want to remove ${member.name}?", style: GoogleFonts.outfit(color: Colors.white54)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text("CANCEL", style: GoogleFonts.outfit(color: Colors.white54))),
          TextButton(onPressed: () => Navigator.pop(context, true), child: Text("DELETE", style: GoogleFonts.outfit(color: Colors.redAccent, fontWeight: FontWeight.bold))),
        ],
      ),
    ) ?? false;

    if (!confirm) return;

    setState(() => _isLoading = true);
    try {
      // 1. Determine S3 paths to delete
      List<String> pathsToDelete = [];
      if (member.imagePaths != null && member.imagePaths!.isNotEmpty) {
        pathsToDelete = member.imagePaths!.whereType<String>().toList();
      } else {
        // Fallback: Reconstruct paths using the family member's email/details and current user email prefix
        try {
          final attributes = await Amplify.Auth.fetchUserAttributes();
          final emailAttr = attributes.firstWhere((attr) => attr.userAttributeKey == AuthUserAttributeKey.email);
          final mainUserEmail = emailAttr.value.split('@')[0].trim().toLowerCase();
          final cleanMemberName = member.name.split('@')[0].trim().replaceAll(' ', '_').toLowerCase();
          
          pathsToDelete = [
            'public/face_entries/${mainUserEmail}_${cleanMemberName}_front.jpg',
            'public/face_entries/${mainUserEmail}_${cleanMemberName}_left.jpg',
            'public/face_entries/${mainUserEmail}_${cleanMemberName}_right.jpg',
          ];
        } catch (authErr) {
          safePrint('Failed to construct fallback S3 paths: $authErr');
        }
      }

      // 2. Delete S3 files first
      for (final path in pathsToDelete) {
        if (path.isNotEmpty) {
          try {
            safePrint('Attempting to delete from S3: $path');
            final result = await Amplify.Storage.remove(
              path: StoragePath.fromString(path),
            ).result;
            safePrint('Successfully deleted photo from S3: ${result.removedItem.path}');
          } catch (storageError) {
            safePrint('Error deleting photo from S3 ($path): $storageError');
          }
        }
      }

      // 3. Delete member from DynamoDB
      final request = ModelMutations.delete(
        member,
        authorizationMode: APIAuthorizationType.userPools,
      );
      final response = await Amplify.API.mutate(request: request).response;

      if (response.hasErrors) {
        throw Exception(response.errors.first.message);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Member Deleted!"), backgroundColor: Colors.green));
      }
      await _loadMembers();
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
          "FAMILY MEMBERS", 
          style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2)
        ).animate(onPlay: (controller) => controller.repeat(reverse: true))
         .shimmer(duration: 2.seconds, color: _accentColor.withOpacity(0.5)),
      ),
      body: Stack(
        children: [
          Positioned(
            bottom: -50, right: -100,
            child: Container(
              width: 300, height: 300,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [_accentColor.withOpacity(0.1), Colors.transparent])),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scaleXY(end: 1.3, duration: 5.seconds, curve: Curves.easeInOut),
          ),
          SafeArea(
            child: _isLoading 
              ? Center(child: CircularProgressIndicator(color: _accentColor))
              : _members.isEmpty
                  ? Center(
                      child: Text(
                        "No family members found.\nAdd a member to the system!", 
                        textAlign: TextAlign.center,
                        style: GoogleFonts.outfit(color: Colors.white54, fontSize: 16)
                      ).animate().fade().slideY(),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _members.length,
                      itemBuilder: (context, index) {
                        final member = _members[index];
                        return _buildMemberCard(member)
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
          await Navigator.push(context, MaterialPageRoute(builder: (context) => const AddFamilyMemberScreen()));
          _loadMembers(); // Reload after coming back
        },
        backgroundColor: _accentColor,
        icon: const Icon(Icons.person_add, color: Colors.black),
        label: Text("ADD MEMBER", style: GoogleFonts.orbitron(color: Colors.black, fontWeight: FontWeight.bold)),
      ).animate(onPlay: (controller) => controller.repeat(reverse: true))
       .boxShadow(
         begin: BoxShadow(color: _accentColor.withOpacity(0.2), blurRadius: 5, spreadRadius: 0),
         end: BoxShadow(color: _accentColor.withOpacity(0.6), blurRadius: 15, spreadRadius: 2),
         duration: 2.seconds,
       ),
    );
  }

  Widget _buildMemberCard(FamilyMember member) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        leading: CircleAvatar(
          backgroundColor: _accentColor.withOpacity(0.2),
          child: Icon(Icons.person, color: _accentColor),
        ),
        title: Text(member.name, style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold)),
        subtitle: Text(member.relationship, style: GoogleFonts.outfit(color: Colors.white54)),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.edit_outlined, color: Colors.blueAccent),
              onPressed: () async {
                final result = await Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => EditFamilyMemberScreen(member: member)),
                );
                if (result == true) {
                  _loadMembers();
                }
              },
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
              onPressed: () => _deleteMember(member),
            ),
          ],
        ),
      ),
    );
  }
}
