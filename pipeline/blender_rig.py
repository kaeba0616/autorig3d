"""Blender에서 실행되는 자동 리깅 스크립트. blender --background --python 으로 호출."""
import bpy
import sys

# numpy import 문제 우회 — Blender 내장 numpy 사용
try:
    import numpy
except ImportError:
    # Blender 번들 numpy 경로 추가
    import os
    for p in sys.path:
        np_path = os.path.join(p, 'numpy')
        if os.path.exists(np_path):
            break

argv = sys.argv
argv = argv[argv.index("--") + 1:]
input_file = argv[0]
output_glb = argv[1]

# 씬 초기화
bpy.ops.wm.read_factory_settings(use_empty=True)

# 파일 형식에 따라 임포트
if input_file.endswith('.glb') or input_file.endswith('.gltf'):
    bpy.ops.import_scene.gltf(filepath=input_file)
elif input_file.endswith('.obj'):
    bpy.ops.wm.obj_import(filepath=input_file)
elif input_file.endswith('.fbx'):
    bpy.ops.import_scene.fbx(filepath=input_file)
else:
    bpy.ops.import_scene.gltf(filepath=input_file)

# 메쉬 오브젝트 찾기
mesh_obj = None
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        mesh_obj = obj
        break

if mesh_obj is None:
    print("ERROR: 메쉬 오브젝트를 찾을 수 없습니다")
    sys.exit(1)

print(f"메쉬 발견: {mesh_obj.name}, 버텍스: {len(mesh_obj.data.vertices)}")

# 메쉬 크기 정규화 (높이 2m 기준)
dims = mesh_obj.dimensions
max_dim = max(dims)
if max_dim > 0:
    scale_factor = 2.0 / max_dim
    mesh_obj.scale = (scale_factor, scale_factor, scale_factor)
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.transform_apply(scale=True)

# 원점을 바닥으로
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
mesh_obj.location.z = mesh_obj.dimensions.z / 2

height = mesh_obj.dimensions.z

# 아마추어(스켈레톤) 생성
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
armature = bpy.context.object
armature.name = "Armature"

edit_bones = armature.data.edit_bones

# 기존 본 삭제
for bone in edit_bones:
    edit_bones.remove(bone)

# 휴머노이드 스켈레톤
bones_def = {
    "Hips":       {"head": (0, 0, height*0.45), "tail": (0, 0, height*0.50)},
    "Spine":      {"head": (0, 0, height*0.50), "tail": (0, 0, height*0.60), "parent": "Hips"},
    "Chest":      {"head": (0, 0, height*0.60), "tail": (0, 0, height*0.72), "parent": "Spine"},
    "Neck":       {"head": (0, 0, height*0.72), "tail": (0, 0, height*0.80), "parent": "Chest"},
    "Head":       {"head": (0, 0, height*0.80), "tail": (0, 0, height*1.0),  "parent": "Neck"},

    "Shoulder.L": {"head": (0, 0, height*0.70), "tail": (0.1, 0, height*0.70), "parent": "Chest"},
    "UpperArm.L": {"head": (0.1, 0, height*0.70), "tail": (0.25, 0, height*0.55), "parent": "Shoulder.L"},
    "LowerArm.L": {"head": (0.25, 0, height*0.55), "tail": (0.38, 0, height*0.42), "parent": "UpperArm.L"},
    "Hand.L":     {"head": (0.38, 0, height*0.42), "tail": (0.43, 0, height*0.40), "parent": "LowerArm.L"},

    "Shoulder.R": {"head": (0, 0, height*0.70), "tail": (-0.1, 0, height*0.70), "parent": "Chest"},
    "UpperArm.R": {"head": (-0.1, 0, height*0.70), "tail": (-0.25, 0, height*0.55), "parent": "Shoulder.R"},
    "LowerArm.R": {"head": (-0.25, 0, height*0.55), "tail": (-0.38, 0, height*0.42), "parent": "UpperArm.R"},
    "Hand.R":     {"head": (-0.38, 0, height*0.42), "tail": (-0.43, 0, height*0.40), "parent": "LowerArm.R"},

    "UpperLeg.L": {"head": (0.08, 0, height*0.45), "tail": (0.08, 0, height*0.25), "parent": "Hips"},
    "LowerLeg.L": {"head": (0.08, 0, height*0.25), "tail": (0.08, 0, height*0.05), "parent": "UpperLeg.L"},
    "Foot.L":     {"head": (0.08, 0, height*0.05), "tail": (0.08, -0.08, height*0.0), "parent": "LowerLeg.L"},

    "UpperLeg.R": {"head": (-0.08, 0, height*0.45), "tail": (-0.08, 0, height*0.25), "parent": "Hips"},
    "LowerLeg.R": {"head": (-0.08, 0, height*0.25), "tail": (-0.08, 0, height*0.05), "parent": "UpperLeg.R"},
    "Foot.R":     {"head": (-0.08, 0, height*0.05), "tail": (-0.08, -0.08, height*0.0), "parent": "LowerLeg.R"},
}

created_bones = {}
for name, data in bones_def.items():
    bone = edit_bones.new(name)
    bone.head = data["head"]
    bone.tail = data["tail"]
    created_bones[name] = bone

# 부모 설정
for name, data in bones_def.items():
    if "parent" in data:
        created_bones[name].parent = created_bones[data["parent"]]

# 오브젝트 모드로 돌아가기
bpy.ops.object.mode_set(mode='OBJECT')

# 메쉬를 아마추어에 페어런트 + 자동 웨이트
bpy.ops.object.select_all(action='DESELECT')
mesh_obj.select_set(True)
armature.select_set(True)
bpy.context.view_layer.objects.active = armature
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

print(f"리깅 완료: {len(created_bones)}개 본")

# 내보내기 — GLB를 시도하고, 실패하면 FBX로 폴백
export_ok = False
try:
    bpy.ops.export_scene.gltf(
        filepath=output_glb,
        export_format='GLB',
        use_selection=False,
        export_animations=False,
    )
    export_ok = True
    print(f"내보내기 완료 (GLB): {output_glb}")
except Exception as e:
    print(f"GLB 내보내기 실패: {e}, FBX로 폴백")

if not export_ok:
    # FBX로 폴백
    fbx_path = output_glb.replace('.glb', '.fbx')
    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
        use_selection=False,
        add_leaf_bones=False,
        path_mode='COPY',
        embed_textures=True,
    )
    print(f"내보내기 완료 (FBX): {fbx_path}")

    # FBX를 다시 GLB로 변환 시도 (클린 씬)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    try:
        bpy.ops.export_scene.gltf(
            filepath=output_glb,
            export_format='GLB',
            use_selection=False,
            export_animations=False,
        )
        print(f"FBX→GLB 변환 완료: {output_glb}")
    except Exception as e2:
        print(f"FBX→GLB 변환도 실패: {e2}")
        print(f"FBX_FALLBACK: {fbx_path}")
