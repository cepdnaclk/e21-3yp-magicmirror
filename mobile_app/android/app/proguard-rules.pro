# Amplify & Google Crypto Tink missing classes fix
-dontwarn com.google.errorprone.annotations.**
-dontwarn javax.annotation.**
-dontwarn org.checkerframework.**
-dontwarn com.google.j2objc.annotations.**

# Keep rules for Tink
-keep class com.google.crypto.tink.** { *; }