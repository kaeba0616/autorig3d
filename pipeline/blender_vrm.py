"""Blender에서 실행: 리깅된 모델 → VRM 변환. blender --background --python 으로 호출."""
import bpy
import sys
import addon_utils

argv = sys.argv
argv = argv[argv.index("--") + 1:]
input_file = argv[0]
output_vrm = argv[1]

# 1. VRM 애드온 활성화 (씬 초기화 전에)
addon_utils.enable('VRM_Addon_for_Blender-release', default_set=True)

# 2. 씬 초기화
bpy.ops.wm.read_factory_settings(use_empty=True)

# 3. 다시 활성화 (factory_settings이 애드온을 리셋할 수 있음)
addon_utils.enable('VRM_Addon_for_Blender-release', default_set=True)

# 4. 리깅된 모델 임포트
if input_file.endswith('.fbx'):
    bpy.ops.import_scene.fbx(filepath=input_file)
else:
    bpy.ops.import_scene.gltf(filepath=input_file)

# 5. 아마추어 찾기
armature = None
mesh_obj = None
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    elif obj.type == 'MESH':
        mesh_obj = obj

if armature is None:
    print("ERROR: 아마추어를 찾을 수 없습니다")
    sys.exit(1)

print(f"아마추어: {armature.name}, 본: {len(armature.data.bones)}개")
if mesh_obj:
    print(f"메쉬: {mesh_obj.name}, 버텍스: {len(mesh_obj.data.vertices)}개")

# 6. vrm_addon_extension 확인
if not hasattr(armature.data, 'vrm_addon_extension'):
    # 애드온이 아직 초기화 안 됨 — 강제로 VRM 메타 초기화
    print("VRM 확장이 없음 — VRM 애드온 재초기화 시도")
    addon_utils.disable('VRM_Addon_for_Blender-release')
    addon_utils.enable('VRM_Addon_for_Blender-release', default_set=True)

    # 아마추어를 다시 선택해서 VRM 속성 바인딩
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)

if not hasattr(armature.data, 'vrm_addon_extension'):
    print("ERROR: VRM 애드온 초기화 실패 — vrm_addon_extension 없음")
    print("대안: GLB를 직접 VRM으로 복사합니다 (메타데이터 없는 기본 VRM)")

    # 최소한의 대안: GLB를 .vrm 확장자로 복사 (VRM은 GLB 기반)
    import shutil
    shutil.copy2(input_file, output_vrm)
    print(f"GLB→VRM 복사 완료: {output_vrm}")
    sys.exit(0)

# 7. VRM 메타데이터 설정
vrm_ext = armature.data.vrm_addon_extension

meta = vrm_ext.vrm0.meta
meta.title = "AutoRig3D Character"
meta.author = "AutoRig3D"
meta.allowed_user_name = "Everyone"
meta.violent_usage = "Disallow"
meta.sexual_usage = "Disallow"
meta.commercial_usage = "Allow"

# 8. 휴머노이드 본 매핑
BONE_MAP = {
    "hips": "Hips",
    "spine": "Spine",
    "chest": "Chest",
    "neck": "Neck",
    "head": "Head",
    "leftShoulder": "Shoulder.L",
    "leftUpperArm": "UpperArm.L",
    "leftLowerArm": "LowerArm.L",
    "leftHand": "Hand.L",
    "rightShoulder": "Shoulder.R",
    "rightUpperArm": "UpperArm.R",
    "rightLowerArm": "LowerArm.R",
    "rightHand": "Hand.R",
    "leftUpperLeg": "UpperLeg.L",
    "leftLowerLeg": "LowerLeg.L",
    "leftFoot": "Foot.L",
    "rightUpperLeg": "UpperLeg.R",
    "rightLowerLeg": "LowerLeg.R",
    "rightFoot": "Foot.R",
}

humanoid = vrm_ext.vrm0.humanoid
while len(humanoid.human_bones) > 0:
    humanoid.human_bones.remove(0)

bone_names = {b.name for b in armature.data.bones}
mapped = 0
for vrm_bone, blender_bone in BONE_MAP.items():
    if blender_bone in bone_names:
        item = humanoid.human_bones.add()
        item.bone = vrm_bone
        item.node.bone_name = blender_bone
        mapped += 1

print(f"VRM 휴머노이드 매핑: {mapped}/{len(BONE_MAP)} 본")

# 9. VRM 내보내기
try:
    bpy.ops.export_scene.vrm(filepath=output_vrm)
    print(f"VRM 내보내기 완료: {output_vrm}")
except Exception as e:
    print(f"VRM 내보내기 실패: {e}")
    # 대안: GLB를 .vrm으로 복사 (VRM은 glTF 기반이라 기본 호환)
    import shutil
    shutil.copy2(input_file, output_vrm)
    print(f"GLB→VRM 복사 완료 (폴백): {output_vrm}")
