"""Blender에서 실행: 리깅된 모델 → VRM 변환. blender --background --python 으로 호출."""
import bpy
import sys
import addon_utils

argv = sys.argv
argv = argv[argv.index("--") + 1:]
input_file = argv[0]
output_vrm = argv[1]

# VRM 애드온 활성화
addon_utils.enable('VRM_Addon_for_Blender-release', default_set=True)

# 씬 초기화
bpy.ops.wm.read_factory_settings(use_empty=True)

# 리깅된 모델 임포트
if input_file.endswith('.glb') or input_file.endswith('.gltf'):
    bpy.ops.import_scene.gltf(filepath=input_file)
elif input_file.endswith('.fbx'):
    bpy.ops.import_scene.fbx(filepath=input_file)
else:
    bpy.ops.import_scene.gltf(filepath=input_file)

# 아마추어 찾기
armature = None
mesh_obj = None
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    elif obj.type == 'MESH':
        mesh_obj = obj

if armature is None:
    print("ERROR: 아마추어를 찾을 수 없습니다. 리깅된 모델이 아닙니다.")
    sys.exit(1)

print(f"아마추어: {armature.name}, 본: {len(armature.data.bones)}개")
if mesh_obj:
    print(f"메쉬: {mesh_obj.name}, 버텍스: {len(mesh_obj.data.vertices)}개")

# VRM 메타데이터 설정
vrm_ext = armature.data.vrm_addon_extension

# VRM 0.x 메타데이터
meta = vrm_ext.vrm0.meta
meta.title = "AutoRig3D Character"
meta.author = "AutoRig3D"
meta.allowed_user_name = "Everyone"
meta.violent_usage = "Disallow"
meta.sexual_usage = "Disallow"
meta.commercial_usage = "Allow"

# 본 이름 → VRM 휴머노이드 매핑
# VRM은 표준 휴머노이드 본 이름을 요구함
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

# 휴머노이드 본 매핑 설정
humanoid = vrm_ext.vrm0.humanoid
# 기존 매핑 클리어
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

# VRM 내보내기
try:
    bpy.ops.export_scene.vrm(filepath=output_vrm)
    print(f"VRM 내보내기 완료: {output_vrm}")
except Exception as e:
    print(f"VRM 내보내기 실패: {e}")
    # VRM 1.0으로 재시도
    try:
        bpy.ops.export_scene.vrm(filepath=output_vrm, vrm_version='VRM_1_0')
        print(f"VRM 1.0 내보내기 완료: {output_vrm}")
    except Exception as e2:
        print(f"VRM 1.0도 실패: {e2}")
        sys.exit(1)
