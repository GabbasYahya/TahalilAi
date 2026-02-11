import os
import sys
import time

# Add the current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analyze_results_v2 import analyze_image

def test_analysis():
    # Path to a test image
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, "uploads", "test.png")
    
    if not os.path.exists(image_path):
        # Try the other one if test.png doesn't exist
        image_path = os.path.join(base_dir, "uploads", "Resultats-de-laboratoire-pathologiques-a-ladmission.png")
    
    if not os.path.exists(image_path):
        print(f"Error: No test image found at {image_path}")
        return

    print(f"Starting analysis on {image_path}...")
    start_time = time.time()
    
    try:
        # Mocking age and gender
        result = analyze_image(image_path, age="30", gender="Male")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*30)
        print(f"Analysis completed in {duration:.2f} seconds")
        print("Result preview:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print("="*30)
        
    except Exception as e:
        print(f"Analysis failed: {e}")

if __name__ == "__main__":
    test_analysis()
