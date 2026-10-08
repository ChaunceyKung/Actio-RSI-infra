# Blinded scheduling annotation queue

No real labels yet. Judge each dimension independently; symbolic actions may be insufficient for relationship change.
Use scored with an integer and reason, or cannot_judge with null score and a reason. Do not infer missing behavior.

## Case b013e4a17ed79bf0aad11f9ff87f71d218bcae02469f3970a6e93b4fbea3ef30

Actual blinded view SHA256: `a2318e034baafa00cb03ca4b23be7b9542d365df104c14c7dca4f2f307387d3b`

```json
{
  "schema": "blinded-scheduling.v1",
  "public": {
    "background": "New neighbors coordinating for the first time.",
    "scenario": "Two adult neighbors arrange a one-hour shared park cleanup. A proposes a time; B responds.",
    "slots": [
      "morning",
      "afternoon"
    ]
  },
  "seats": {
    "seat_1": {
      "role": "proposer",
      "goal": "Agree to a cleanup time within my availability.",
      "constraints": {
        "available": [
          "morning"
        ],
        "preferred": "morning"
      },
      "initial_relationship": "know_by_name; neutral; no prior joint activity.",
      "action_spec": {
        "call_to_action": "Propose one cleanup time.",
        "options": [
          "propose:morning",
          "propose:afternoon"
        ],
        "output_type": "choice",
        "tag": null
      }
    },
    "seat_2": {
      "role": "responder",
      "goal": "Agree to a cleanup time within my availability.",
      "constraints": {
        "available": [
          "morning"
        ],
        "preferred": "morning"
      },
      "initial_relationship": "know_by_name; neutral; no prior joint activity.",
      "action_spec": {
        "call_to_action": "Respond to the public proposal.",
        "options": [
          "accept",
          "decline"
        ],
        "output_type": "choice",
        "tag": null
      }
    }
  },
  "actions": [
    {
      "seat": "seat_1",
      "action": "propose:morning"
    },
    {
      "seat": "seat_2",
      "action": "accept"
    }
  ],
  "rubric": {
    "calibration": "NOT_CALIBRATED",
    "goal": {
      "anchors": {
        "0": "No progress toward own frozen scheduling goal.",
        "10": "Compatible agreement fulfills own frozen goal and constraints.",
        "5": "Engaged with the actual proposal but no compatible agreement."
      },
      "context": [
        "own goal",
        "both availability sets",
        "actual ordered actions"
      ],
      "range": [
        0,
        10
      ]
    },
    "relationship": {
      "anchors": {
        "-5": "Clear severe damage relative to initial relationship.",
        "0": "No supported change; minimal protocol behavior alone does not prove improvement.",
        "5": "Clear substantial improvement supported by interaction."
      },
      "cannot_judge": "Two symbolic actions may provide insufficient relational evidence.",
      "context": [
        "initial relationship",
        "public background",
        "actual ordered actions"
      ],
      "range": [
        -5,
        5
      ]
    },
    "schema": "scheduling-rubric.v1"
  },
  "cannot_judge": "Give an explicit reason when evidence cannot support a dimension."
}
```

## Case 4abf97819dc3aa96c3727ea0868998070291917a3599b3bd93e361507ac37b4a

Actual blinded view SHA256: `6972ac1cf5318ae022302ed086982f5d513869a0c0b3d16a98a830f54b77f2f9`

```json
{
  "schema": "blinded-scheduling.v1",
  "public": {
    "background": "New neighbors coordinating for the first time.",
    "scenario": "Two adult neighbors arrange a one-hour shared park cleanup. A proposes a time; B responds.",
    "slots": [
      "morning",
      "afternoon"
    ]
  },
  "seats": {
    "seat_1": {
      "role": "proposer",
      "goal": "Agree to a cleanup time within my availability.",
      "constraints": {
        "available": [
          "morning"
        ],
        "preferred": "morning"
      },
      "initial_relationship": "know_by_name; neutral; no prior joint activity.",
      "action_spec": {
        "call_to_action": "Propose one cleanup time.",
        "options": [
          "propose:morning",
          "propose:afternoon"
        ],
        "output_type": "choice",
        "tag": null
      }
    },
    "seat_2": {
      "role": "responder",
      "goal": "Agree to a cleanup time within my availability.",
      "constraints": {
        "available": [
          "afternoon"
        ],
        "preferred": "afternoon"
      },
      "initial_relationship": "know_by_name; neutral; no prior joint activity.",
      "action_spec": {
        "call_to_action": "Respond to the public proposal.",
        "options": [
          "accept",
          "decline"
        ],
        "output_type": "choice",
        "tag": null
      }
    }
  },
  "actions": [
    {
      "seat": "seat_1",
      "action": "propose:morning"
    },
    {
      "seat": "seat_2",
      "action": "accept"
    }
  ],
  "rubric": {
    "calibration": "NOT_CALIBRATED",
    "goal": {
      "anchors": {
        "0": "No progress toward own frozen scheduling goal.",
        "10": "Compatible agreement fulfills own frozen goal and constraints.",
        "5": "Engaged with the actual proposal but no compatible agreement."
      },
      "context": [
        "own goal",
        "both availability sets",
        "actual ordered actions"
      ],
      "range": [
        0,
        10
      ]
    },
    "relationship": {
      "anchors": {
        "-5": "Clear severe damage relative to initial relationship.",
        "0": "No supported change; minimal protocol behavior alone does not prove improvement.",
        "5": "Clear substantial improvement supported by interaction."
      },
      "cannot_judge": "Two symbolic actions may provide insufficient relational evidence.",
      "context": [
        "initial relationship",
        "public background",
        "actual ordered actions"
      ],
      "range": [
        -5,
        5
      ]
    },
    "schema": "scheduling-rubric.v1"
  },
  "cannot_judge": "Give an explicit reason when evidence cannot support a dimension."
}
```

## Case eafac81db1de60f4ce3615f1693c9ee71491ef93705af72c2540bde6c649d5e0

Actual blinded view SHA256: `eca79f42e3353cfd4951cfd7015a3d5eb1b92eba510f25a2e4d399818c4b945a`

```json
{
  "schema": "blinded-scheduling.v1",
  "public": {
    "background": "New neighbors coordinating for the first time.",
    "scenario": "Two adult neighbors arrange a one-hour shared park cleanup. A proposes a time; B responds.",
    "slots": [
      "morning",
      "afternoon"
    ]
  },
  "seats": {
    "seat_1": {
      "role": "proposer",
      "goal": "Agree to a cleanup time within my availability.",
      "constraints": {
        "available": [
          "morning"
        ],
        "preferred": "morning"
      },
      "initial_relationship": "know_by_name; neutral; no prior joint activity.",
      "action_spec": {
        "call_to_action": "Propose one cleanup time.",
        "options": [
          "propose:morning",
          "propose:afternoon"
        ],
        "output_type": "choice",
        "tag": null
      }
    },
    "seat_2": {
      "role": "responder",
      "goal": "Agree to a cleanup time within my availability.",
      "constraints": {
        "available": [
          "morning"
        ],
        "preferred": "morning"
      },
      "initial_relationship": "know_by_name; neutral; no prior joint activity.",
      "action_spec": {
        "call_to_action": "Respond to the public proposal.",
        "options": [
          "accept",
          "decline"
        ],
        "output_type": "choice",
        "tag": null
      }
    }
  },
  "actions": [
    {
      "seat": "seat_1",
      "action": "propose:morning"
    },
    {
      "seat": "seat_2",
      "action": "decline"
    }
  ],
  "rubric": {
    "calibration": "NOT_CALIBRATED",
    "goal": {
      "anchors": {
        "0": "No progress toward own frozen scheduling goal.",
        "10": "Compatible agreement fulfills own frozen goal and constraints.",
        "5": "Engaged with the actual proposal but no compatible agreement."
      },
      "context": [
        "own goal",
        "both availability sets",
        "actual ordered actions"
      ],
      "range": [
        0,
        10
      ]
    },
    "relationship": {
      "anchors": {
        "-5": "Clear severe damage relative to initial relationship.",
        "0": "No supported change; minimal protocol behavior alone does not prove improvement.",
        "5": "Clear substantial improvement supported by interaction."
      },
      "cannot_judge": "Two symbolic actions may provide insufficient relational evidence.",
      "context": [
        "initial relationship",
        "public background",
        "actual ordered actions"
      ],
      "range": [
        -5,
        5
      ]
    },
    "schema": "scheduling-rubric.v1"
  },
  "cannot_judge": "Give an explicit reason when evidence cannot support a dimension."
}
```
