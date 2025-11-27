const fs = require('fs');
const path = require('path');

function processFadeFiles(dirPath) {
    const files = fs.readdirSync(dirPath);
    for (const file of files) {
        const filePath = path.join(dirPath, file);
        const stat = fs.statSync(filePath);
        if (stat.isDirectory()) {
            processFadeFiles(filePath);
        } else if (file.endsWith('.fade.json')) {
            const fileName = path.basename(file, '.fade.json');
            const data = fs.readFileSync(filePath, 'utf8');
            const obj = JSON.parse(data);
            const motion3Json = {
                'Version': 3,
                "Meta": {
                    "Duration": 0.000,
                    "Fps": 60.0,
                    "Loop": true,
                    "AreBeziersRestricted": true,
                    "CurveCount": 0,
                    "TotalSegmentCount": 0,
                    "TotalPointCount": 0,
                    "UserDataCount": 1,
                    "TotalUserDataSize": 0
                },
                "Curves": [],
                "UserData": [
                    {
                        "Time": 0.0,
                        "Value": ""
                    }
                ]
            };
            
            let TotalSegmentCount = 0
            let maxTime = 0.0
            for (let i = 0; i < obj.ParameterCurves.length; i++) {
                let Segments = []
                for (let j = 0; j < obj.ParameterCurves[i].m_Curve.length; j++) {
                    TotalSegmentCount++;
                    Segments.push(obj.ParameterCurves[i].m_Curve[j].time ?? 0)
                    Segments.push(obj.ParameterCurves[i].m_Curve[j].value ?? 0)
                    Segments.push(obj.ParameterCurves[i].m_Curve[j].weightedMode ?? 0)
                    maxTime = maxTime > obj.ParameterCurves[i].m_Curve[j].time ? maxTime : obj.ParameterCurves[i].m_Curve[j].time
                }
                Segments.pop()
                motion3Json.Curves.push({
                    "Target": "Parameter",
                    "Id": obj.ParameterIdHashes[i],
                    "Segments": Segments
                })
            }
            motion3Json.Meta.CurveCount = obj.ParameterIdHashes.length
            motion3Json.Meta.Duration = maxTime
            motion3Json.Meta.TotalSegmentCount = TotalSegmentCount
            motion3Json.Meta.TotalPointCount = obj.ParameterIdHashes.length + TotalSegmentCount
            fs.writeFileSync(path.join(dirPath, `${fileName}.motion3.json`), JSON.stringify(motion3Json, '\t'));
            console.log(path.join(dirPath, `${fileName}.motion3.json`) + "已生成");
        } else if (file.endsWith('CubismPhysicsController.json')) {
            const data = fs.readFileSync(filePath, 'utf8');
            const obj = JSON.parse(data);
            let physicsJson = {
                "Version": 3,
                "Meta": {
                    "PhysicsSettingCount": 0,
                    "TotalInputCount": 0,
                    "TotalOutputCount": 0,
                    "VertexCount": 0,
                    "Fps": 0,
                    "EffectiveForces": {
                    },
                    "PhysicsDictionary": [
                    ]
                },
                "PhysicsSettings": []
            }
            physicsJson.Meta.EffectiveForces.Gravity = obj?._rig?.Gravity
            physicsJson.Meta.EffectiveForces.Wind = obj?._rig?.Wind
            physicsJson.Meta.Fps = obj._rig.Fps ?? 60
            for (let i = 0; i < obj._rig?.SubRigs?.length ?? 0; i++) {
                let physicsSetting = {
                    "Id": "PhysicsSetting",
                    "Input": [
                    ],
                    "Output": [
                    ],
                    "Vertices": [
                    ],
                    "Normalization": {
                    }
                }
                let rig = obj._rig.SubRigs[i]
                physicsSetting.Id = physicsSetting.Id + (i + 1)
                physicsJson.Meta.PhysicsDictionary.push({
                    "Id": physicsSetting.Id,
                    "Name": i + 1 + ""
                })
                for (let j = 0; j < rig?.Input.length ?? 0; j++) {
                    physicsSetting.Input.push({
                        "Source": {
                            "Target": "Parameter",
                            "Id": rig.Input[j].SourceId
                        },
                        "Weight": rig.Input[j].Weight,
                        "Type": rig.Input[j].AngleScale || rig.Input[j].AngleScale === 0 ? "Angle" : "X",
                        "Reflect": false
                    })
                }
                for (let j = 0; j < rig?.Output.length ?? 0; j++) {
                    physicsSetting.Output.push({
                        "Destination": {
                            "Target": "Parameter",
                            "Id": rig.Output[j].DestinationId
                        },
                        "VertexIndex": 1,
                        "Scale": rig.Output[j].AngleScale ?? 1,
                        "Weight": rig.Output[j].Weight,
                        "Type": rig.Output[j].AngleScale || rig.Output[j].AngleScale === 0 ? "Angle" : "X",
                        "Reflect": false
                    })
                }
                for(let j = 0; j < rig?.Particles?.length; j++) {
                    physicsSetting.Vertices.push(                        {
                        "Position": rig?.Particles[j].InitialPosition,
                        "Mobility": rig?.Particles[j].Mobility,
                        "Delay": rig?.Particles[j].Delay,
                        "Acceleration": rig?.Particles[j].Acceleration,
                        "Radius": rig?.Particles[j].Radius
                    })
                }
                physicsSetting.Normalization = rig.Normalization
                physicsJson.PhysicsSettings.push(physicsSetting)
            }
            fs.writeFileSync(path.join(dirPath, `l2d.physics3.json`), JSON.stringify(physicsJson, '\t'));
            console.log(path.join(dirPath, `l2d.physics3.json`) + "已生成");
        }
    }
}

processFadeFiles(__dirname);