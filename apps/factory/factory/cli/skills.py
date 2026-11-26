from pathlib import Path
import yaml

SKILL_DIRS = [
    Path.cwd()/ ".agents" / "skills",
    Path.home()/ ".agents" / "skills",
]

def find_skills():
    """Map each skill name to its description and SKILL.md path."""
    skills = {}
    for skill_dir in SKILL_DIRS:
        if not skill_dir.exists():
            continue
        for skill_path in sorted(skill_dir.glob("*/SKILL.md")):
            _, frontmatter, _ = skill_path.read_text().split('---\n', 2)
            meta_data = yaml.safe_load(frontmatter)
            description = " ".join(meta_data.get("description", "").split())
            skills[meta_data["name"]] = {
                "description": description,
                "path": skill_path
            }
    return skills

SKILLS = find_skills()

def skills_prompt():
    return "\n".join(f"{name}: {info['description']}" for name, info in SKILLS.items())

def read_skill(name: str) -> str:
    """Open a skil and return its full instructions."""
    if name not in SKILLS:
        return f"No skill found with name '{name}'"

    return SKILLS[name]["path"].read_text()

# if __name__ == "__main__":
#     print(skills_prompt())