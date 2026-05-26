# Amplify & Google Crypto Tink missing classes fix
-dontwarn com.google.errorprone.annotations.**
-dontwarn javax.annotation.**
-dontwarn org.checkerframework.**
-dontwarn com.google.j2objc.annotations.**
-dontwarn com.google.api.client.**
-dontwarn com.google.crypto.tink.**
-dontwarn org.joda.time.**

# Keep rules for Tink
-keep class com.google.crypto.tink.** { *; }