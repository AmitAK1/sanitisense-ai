"""
Quick LaTeX Template Filler
Simple script to fill the presentation with your data
"""

def fill_presentation():
    """Interactive script to fill the presentation template"""
    
    print("=" * 60)
    print("AWS AI for Bharat Hackathon - Presentation Filler")
    print("=" * 60)
    print()
    
    # Read the template
    with open("Docs/SanitiSense_AI_Presentation.tex", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get user inputs
    print("Please provide the following information:")
    print()
    
    project_name = input("1. Project Name [SanitiSense AI]: ").strip() or "SanitiSense AI"
    team_leader = input("2. Team Leader Name: ").strip()
    
    # Replace in template
    if team_leader:
        content = content.replace('<Your Name>', team_leader)
    
    # You can customize the project name if different
    if project_name != "SanitiSense AI":
        content = content.replace('SanitiSense AI', project_name)
    
    # Save the filled template
    output_path = "Docs/Filled_Presentation.tex"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print()
    print("=" * 60)
    print(f"✓ Success! Filled template saved to: {output_path}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Open the file in a LaTeX editor (Overleaf, TeXstudio, etc.)")
    print("2. Compile to PDF using: pdflatex")
    print("3. Review and make any additional customizations")
    print()

if __name__ == "__main__":
    fill_presentation()
