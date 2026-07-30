/*
* Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
*
* Licensed under the Apache License, Version 2.0 (the "License").
* You may not use this file except in compliance with the License.
* A copy of the License is located at
*
*  http://aws.amazon.com/apache2.0
*
* or in the "license" file accompanying this file. This file is distributed
* on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
* express or implied. See the License for the specific language governing
* permissions and limitations under the License.
*/

// NOTE: This file is generated and may not follow lint rules defined in your app
// Generated files can be excluded from analysis in analysis_options.yaml
// For more info, see: https://dart.dev/guides/language/analysis-options#excluding-code-from-analysis

// ignore_for_file: public_member_api_docs, annotate_overrides, dead_code, dead_codepublic_member_api_docs, depend_on_referenced_packages, file_names, library_private_types_in_public_api, no_leading_underscores_for_library_prefixes, no_leading_underscores_for_local_identifiers, non_constant_identifier_names, null_check_on_nullable_type_parameter, override_on_non_overriding_member, prefer_adjacent_string_concatenation, prefer_const_constructors, prefer_if_null_operators, prefer_interpolation_to_compose_strings, slash_for_doc_comments, sort_child_properties_last, unnecessary_const, unnecessary_constructor_name, unnecessary_late, unnecessary_new, unnecessary_null_aware_assignments, unnecessary_nullable_for_final_variable_declarations, unnecessary_string_interpolations, use_build_context_synchronously

import 'ModelProvider.dart';
import 'package:amplify_core/amplify_core.dart' as amplify_core;
import 'package:collection/collection.dart';


/** This is an auto generated class representing the FamilyMember type in your schema. */
class FamilyMember extends amplify_core.Model {
  static const classType = const _FamilyMemberModelType();
  final String id;
  final String? _name;
  final String? _relationship;
  final List<String>? _imagePaths;
  final amplify_core.TemporalDateTime? _createdAt;
  final amplify_core.TemporalDateTime? _updatedAt;

  @override
  getInstanceType() => classType;
  
  @Deprecated('[getId] is being deprecated in favor of custom primary key feature. Use getter [modelIdentifier] to get model identifier.')
  @override
  String getId() => id;
  
  FamilyMemberModelIdentifier get modelIdentifier {
      return FamilyMemberModelIdentifier(
        id: id
      );
  }
  
  String get name {
    try {
      return _name!;
    } catch(e) {
      throw amplify_core.AmplifyCodeGenModelException(
          amplify_core.AmplifyExceptionMessages.codeGenRequiredFieldForceCastExceptionMessage,
          recoverySuggestion:
            amplify_core.AmplifyExceptionMessages.codeGenRequiredFieldForceCastRecoverySuggestion,
          underlyingException: e.toString()
          );
    }
  }
  
  String get relationship {
    try {
      return _relationship!;
    } catch(e) {
      throw amplify_core.AmplifyCodeGenModelException(
          amplify_core.AmplifyExceptionMessages.codeGenRequiredFieldForceCastExceptionMessage,
          recoverySuggestion:
            amplify_core.AmplifyExceptionMessages.codeGenRequiredFieldForceCastRecoverySuggestion,
          underlyingException: e.toString()
          );
    }
  }
  
  List<String>? get imagePaths {
    return _imagePaths;
  }
  
  amplify_core.TemporalDateTime? get createdAt {
    return _createdAt;
  }
  
  amplify_core.TemporalDateTime? get updatedAt {
    return _updatedAt;
  }
  
  const FamilyMember._internal({required this.id, required name, required relationship, imagePaths, createdAt, updatedAt}): _name = name, _relationship = relationship, _imagePaths = imagePaths, _createdAt = createdAt, _updatedAt = updatedAt;
  
  factory FamilyMember({String? id, required String name, required String relationship, List<String>? imagePaths}) {
    return FamilyMember._internal(
      id: id == null ? amplify_core.UUID.getUUID() : id,
      name: name,
      relationship: relationship,
      imagePaths: imagePaths != null ? List<String>.unmodifiable(imagePaths) : imagePaths);
  }
  
  bool equals(Object other) {
    return this == other;
  }
  
  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is FamilyMember &&
      id == other.id &&
      _name == other._name &&
      _relationship == other._relationship &&
      DeepCollectionEquality().equals(_imagePaths, other._imagePaths);
  }
  
  @override
  int get hashCode => toString().hashCode;
  
  @override
  String toString() {
    var buffer = new StringBuffer();
    
    buffer.write("FamilyMember {");
    buffer.write("id=" + "$id" + ", ");
    buffer.write("name=" + "$_name" + ", ");
    buffer.write("relationship=" + "$_relationship" + ", ");
    buffer.write("imagePaths=" + (_imagePaths != null ? _imagePaths!.toString() : "null") + ", ");
    buffer.write("createdAt=" + (_createdAt != null ? _createdAt!.format() : "null") + ", ");
    buffer.write("updatedAt=" + (_updatedAt != null ? _updatedAt!.format() : "null"));
    buffer.write("}");
    
    return buffer.toString();
  }
  
  FamilyMember copyWith({String? name, String? relationship, List<String>? imagePaths}) {
    return FamilyMember._internal(
      id: id,
      name: name ?? this.name,
      relationship: relationship ?? this.relationship,
      imagePaths: imagePaths ?? this.imagePaths);
  }
  
  FamilyMember copyWithModelFieldValues({
    ModelFieldValue<String>? name,
    ModelFieldValue<String>? relationship,
    ModelFieldValue<List<String>?>? imagePaths
  }) {
    return FamilyMember._internal(
      id: id,
      name: name == null ? this.name : name.value,
      relationship: relationship == null ? this.relationship : relationship.value,
      imagePaths: imagePaths == null ? this.imagePaths : imagePaths.value
    );
  }
  
  FamilyMember.fromJson(Map<String, dynamic> json)  
    : id = json['id'],
      _name = json['name'],
      _relationship = json['relationship'],
      _imagePaths = json['imagePaths']?.cast<String>(),
      _createdAt = json['createdAt'] != null ? amplify_core.TemporalDateTime.fromString(json['createdAt']) : null,
      _updatedAt = json['updatedAt'] != null ? amplify_core.TemporalDateTime.fromString(json['updatedAt']) : null;
  
  Map<String, dynamic> toJson() => {
    'id': id, 'name': _name, 'relationship': _relationship, 'imagePaths': _imagePaths, 'createdAt': _createdAt?.format(), 'updatedAt': _updatedAt?.format()
  };
  
  Map<String, Object?> toMap() => {
    'id': id,
    'name': _name,
    'relationship': _relationship,
    'imagePaths': _imagePaths,
    'createdAt': _createdAt,
    'updatedAt': _updatedAt
  };

  static final amplify_core.QueryModelIdentifier<FamilyMemberModelIdentifier> MODEL_IDENTIFIER = amplify_core.QueryModelIdentifier<FamilyMemberModelIdentifier>();
  static final ID = amplify_core.QueryField(fieldName: "id");
  static final NAME = amplify_core.QueryField(fieldName: "name");
  static final RELATIONSHIP = amplify_core.QueryField(fieldName: "relationship");
  static final IMAGEPATHS = amplify_core.QueryField(fieldName: "imagePaths");
  static var schema = amplify_core.Model.defineSchema(define: (amplify_core.ModelSchemaDefinition modelSchemaDefinition) {
    modelSchemaDefinition.name = "FamilyMember";
    modelSchemaDefinition.pluralName = "FamilyMembers";
    
    modelSchemaDefinition.authRules = [
      amplify_core.AuthRule(
        authStrategy: amplify_core.AuthStrategy.OWNER,
        ownerField: "owner",
        identityClaim: "cognito:username",
        provider: amplify_core.AuthRuleProvider.USERPOOLS,
        operations: const [
          amplify_core.ModelOperation.CREATE,
          amplify_core.ModelOperation.UPDATE,
          amplify_core.ModelOperation.DELETE,
          amplify_core.ModelOperation.READ
        ])
    ];
    
    modelSchemaDefinition.addField(amplify_core.ModelFieldDefinition.id());
    
    modelSchemaDefinition.addField(amplify_core.ModelFieldDefinition.field(
      key: FamilyMember.NAME,
      isRequired: true,
      ofType: amplify_core.ModelFieldType(amplify_core.ModelFieldTypeEnum.string)
    ));
    
    modelSchemaDefinition.addField(amplify_core.ModelFieldDefinition.field(
      key: FamilyMember.RELATIONSHIP,
      isRequired: true,
      ofType: amplify_core.ModelFieldType(amplify_core.ModelFieldTypeEnum.string)
    ));
    
    modelSchemaDefinition.addField(amplify_core.ModelFieldDefinition.field(
      key: FamilyMember.IMAGEPATHS,
      isRequired: false,
      isArray: true,
      ofType: amplify_core.ModelFieldType(amplify_core.ModelFieldTypeEnum.collection, ofModelName: amplify_core.ModelFieldTypeEnum.string.name)
    ));
    
    modelSchemaDefinition.addField(amplify_core.ModelFieldDefinition.nonQueryField(
      fieldName: 'createdAt',
      isRequired: false,
      isReadOnly: true,
      ofType: amplify_core.ModelFieldType(amplify_core.ModelFieldTypeEnum.dateTime)
    ));
    
    modelSchemaDefinition.addField(amplify_core.ModelFieldDefinition.nonQueryField(
      fieldName: 'updatedAt',
      isRequired: false,
      isReadOnly: true,
      ofType: amplify_core.ModelFieldType(amplify_core.ModelFieldTypeEnum.dateTime)
    ));
  });
}

class _FamilyMemberModelType extends amplify_core.ModelType<FamilyMember> {
  const _FamilyMemberModelType();
  
  @override
  FamilyMember fromJson(Map<String, dynamic> jsonData) {
    return FamilyMember.fromJson(jsonData);
  }
  
  @override
  String modelName() {
    return 'FamilyMember';
  }
}

/**
 * This is an auto generated class representing the model identifier
 * of [FamilyMember] in your schema.
 */
class FamilyMemberModelIdentifier implements amplify_core.ModelIdentifier<FamilyMember> {
  final String id;

  /** Create an instance of FamilyMemberModelIdentifier using [id] the primary key. */
  const FamilyMemberModelIdentifier({
    required this.id});
  
  @override
  Map<String, dynamic> serializeAsMap() => (<String, dynamic>{
    'id': id
  });
  
  @override
  List<Map<String, dynamic>> serializeAsList() => serializeAsMap()
    .entries
    .map((entry) => (<String, dynamic>{ entry.key: entry.value }))
    .toList();
  
  @override
  String serializeAsString() => serializeAsMap().values.join('#');
  
  @override
  String toString() => 'FamilyMemberModelIdentifier(id: $id)';
  
  @override
  bool operator ==(Object other) {
    if (identical(this, other)) {
      return true;
    }
    
    return other is FamilyMemberModelIdentifier &&
      id == other.id;
  }
  
  @override
  int get hashCode =>
    id.hashCode;
}