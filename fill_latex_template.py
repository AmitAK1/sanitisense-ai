"""
LaTeX Template Filler for AWS AI for Bharat Hackathon
Fills the presentation template with your project data
"""

import json
import re
from pathlib import Path

class LatexTemplateFiller:
    def __init__(self, template_path, data_path):
        self.template_path = template_path
        self.data_path = data_path
        
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
        
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def fill_template(self):
        """Replace placeholders in the template with actual data"""
        content = self.template_content
        
        # Replace project name (title)
        if 'project_name' in self.data:
            content = content.replace('SanitiSense AI', self.data['project_name'])
        
        # Replace team leader name
        if 'team_leader' in self.data:
            content = content.replace('<Your Name>', self.data['team_leader'])
        
        # Replace problem statement
        if 'problem_statement' in self.data:
            old_problem = 'Residents in underserved communities fail to get sanitation hazards (overflowing drains, garbage accumulation) resolved because municipal systems prioritize formal, written, and categorized grievances, ignoring unstructured photo- and voice-based reports.'
            content = content.replace(old_problem, self.data['problem_statement'])
        
        # Replace core philosophy
        if 'core_philosophy' in self.data:
            old_philosophy = 'Instead of creating another complaint portal, the solution acts as an \\textbf{intelligent translation layer} between citizen reality and municipal systems.'
            new_philosophy = self.data['core_philosophy'].replace('intelligent translation layer', '\\textbf{intelligent translation layer}')
            content = content.replace(old_philosophy, new_philosophy)
        
        return content
    
    def save_filled_template(self, output_path):
        """Save the filled template to a new file"""
        filled_content = self.fill_template()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(filled_content)
        
        print(f"✓ Filled template saved to: {output_path}")

def main():
    template_path = "Docs/SanitiSense_AI_Presentation.tex"
    data_path = "project_data.json"
    output_path = "Docs/Filled_Presentation.tex"
    
    if not Path(data_path).exists():
        print(f"Error: {data_path} not found!")
        print("Please create project_data.json with your project information.")
        print("See project_data_example.json for the structure.")
        return
    
    filler = LatexTemplateFiller(template_path, data_path)
    filler.save_filled_template(output_path)
    
    print("\nNext steps:")
    print("1. Review the filled template: Docs/Filled_Presentation.tex")
    print("2. Compile to PDF using: pdflatex Docs/Filled_Presentation.tex")
    print("   Or use an online LaTeX editor like Overleaf")

if __name__ == "__main__":
    main()
