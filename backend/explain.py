"""
explain.py

Provides human-readable explainability for recommendation results based on
acoustic feature matching.
"""

def get_top_contributors(iem_features: dict[str, float], inferred_target: dict[str, float] = None, top_n: int = 2) -> list[str]:
    """
    Identifies the primary acoustic features driving the match or deviation from neutral.
    """
    
    # We focus on the 7 main frequency bands for simplest explainability.
    bands = ["sub_bass", "bass", "low_mids", "mids", "presence", "treble", "air"]
    
    contributors = []
    
    if inferred_target:
        # Calculate how well the IEM aligns with explicit non-zero target features
        # We score by target * iem_val. Higher score means strong agreement in the same direction.
        scores = {}
        for b in bands:
            tgt = inferred_target.get(b, 0.0)
            val = iem_features.get(b, 0.0)
            # Only consider it a contributor if the target explicitly asked for a deviation
            if abs(tgt) >= 1.0:
                scores[b] = tgt * val
                
        # If we found matches that align with explicit target intent
        if any(v > 0 for v in scores.values()):
            # Sort by highest positive score
            sorted_bands = sorted([b for b in bands if scores.get(b, 0) > 0], key=lambda b: scores.get(b, 0), reverse=True)
            for b in sorted_bands[:top_n]:
                val = iem_features.get(b, 0.0)
                desc = "elevated" if val > 0 else "recessed"
                contributors.append(f"{desc} {b.replace('_', ' ')}")
            return contributors

    # Fallback: if there was no strong explicit acoustic matching 
    # (e.g. target was near 0 or purely semantic match),
    # just describe the most extreme traits of the IEM itself compared to Harman neutral.
    scores = {}
    for b in bands:
        val = iem_features.get(b, 0.0)
        scores[b] = abs(val)
        
    sorted_bands = sorted(bands, key=lambda b: scores[b], reverse=True)
    for b in sorted_bands[:top_n]:
        val = iem_features.get(b, 0.0)
        if val >= 2.0:
            desc = "elevated"
        elif val <= -2.0:
            desc = "recessed"
        else:
            desc = "controlled"
        contributors.append(f"{desc} {b.replace('_', ' ')}")
        
    return contributors
