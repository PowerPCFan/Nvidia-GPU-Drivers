import requests
import json
import urllib.parse

MENU_URL = "https://gfwsl.geforce.com/nvidia_web_services/controller.php?com.nvidia.services.Drivers.getMenuArrays/"
RESULTS = "1"

class NvidiaDriverLookupCLI:
    def __init__(self):
        self.product_families = []
        self.current_series = []
        self.current_products = []
        self.os_options = []
        self.language_options = []

    def make_api_request(self, params=None):
        if params is None:
            params = {}
        
        params_str = json.dumps(params)
        url = f"{MENU_URL}{params_str}"
        
        print(f"Making API request to: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API request failed: {e}")
            return None

    def load_initial_data(self):
        print("Loading initial data...")
        data = self.make_api_request()
        if data and len(data) >= 6:
            self.product_families = data[0] if data[0] else []
            self.os_options = data[4] if data[4] else []
            self.language_options = data[5] if data[5] else []
            print(f"Loaded {len(self.product_families)} product families")
            print(f"Loaded {len(self.os_options)} OS options")
            print(f"Loaded {len(self.language_options)} language options")
            return True
        else:
            print("Failed to load initial data")
            return False

    def load_series_data(self, family_id):
        print(f"Loading series data for family ID: {family_id}")
        data = self.make_api_request({"pt": str(family_id)})
        if data and len(data) > 1 and data[1]:
            self.current_series = data[1]
            print(f"Loaded {len(self.current_series)} series options")
            return True
        else:
            self.current_series = []
            print("Failed to load series data")
            return False

    def load_products_data(self, family_id, series_id):
        print(f"Loading products data for family ID: {family_id}, series ID: {series_id}")
        data = self.make_api_request({"pt": str(family_id), "pst": str(series_id)})
        if data and len(data) > 2:
            # Update products
            if data[2]:
                self.current_products = data[2]
                print(f"Loaded {len(self.current_products)} product options")
            else:
                self.current_products = []
                print("No products found")
            
            # Update OS options if available in response (index 4)
            if len(data) > 4 and data[4]:
                self.os_options = data[4]
                print(f"Updated OS options: {len(self.os_options)} available")
            
            # Update language options if available in response (index 5)
            if len(data) > 5 and data[5]:
                self.language_options = data[5]
                print(f"Updated language options: {len(self.language_options)} available")
            
            return True
        else:
            self.current_products = []
            print("Failed to load products data")
            return False

    def get_id_by_text(self, items, text):
        for item in items:
            if item["menutext"] == text:
                return item["id"]
        return None

    def display_menu(self, items, title):
        print(f"\n{title}:")
        print("-" * len(title))
        for i, item in enumerate(items, 1):
            print(f"{i}. {item['menutext']}")
        return items

    def get_user_choice(self, items, prompt):
        while True:
            try:
                choice = int(input(f"\n{prompt} (1-{len(items)}): ")) - 1
                if 0 <= choice < len(items):
                    return items[choice]
                else:
                    print(f"Please enter a number between 1 and {len(items)}")
            except ValueError:
                print("Please enter a valid number")

    def display_results(self, data):
        if not data or not data.get("Success") or not data.get("IDS"):
            print("\nNo drivers found for the selected configuration.")
            return

        drivers = data["IDS"]
        num_drivers = len(drivers)
        
        print(f"\nFound {num_drivers} Driver{'s' if num_drivers > 1 else ''}!")
        print("=" * 60)
        
        for idx, driver_entry in enumerate(drivers, 1):
            driver_info = driver_entry["downloadInfo"]
            
            print(f"\nDriver {idx} of {num_drivers}")
            print("-" * 40)
            print(f"Name: {urllib.parse.unquote(driver_info.get('Name', 'N/A'))}")
            print(f"Version: {driver_info.get('Version', 'N/A')}")
            print(f"Display Version: {driver_info.get('DisplayVersion', 'N/A')}")
            print(f"Release Date: {driver_info.get('ReleaseDateTime', 'N/A')}")
            print(f"File Size: {driver_info.get('DownloadURLFileSize', 'N/A')}")
            print(f"OS: {urllib.parse.unquote(driver_info.get('OSName', 'N/A'))}")
            print(f"Language: {urllib.parse.unquote(driver_info.get('LanguageName', 'N/A'))}")
            
            # Driver flags
            flags = []
            if driver_info.get('IsBeta') == '1':
                flags.append("Beta")
            if driver_info.get('IsWHQL') == '1':
                flags.append("WHQL")
            if driver_info.get('IsRecommended') == '1':
                flags.append("Recommended")
            if driver_info.get('IsFeaturePreview') == '1':
                flags.append("Feature Preview")
            if driver_info.get('IsNewest') == '1':
                flags.append("Newest")
            if driver_info.get('IsCRD') == '1':
                flags.append("Studio Driver")
            
            print(f"Type: {', '.join(flags) if flags else 'Standard'}")
            
            print(f"\nDownload URL:\n{driver_info.get('DownloadURL', 'N/A')}")
            print(f"\nDetails URL:\n{driver_info.get('DetailsURL', 'N/A')}")
            
            # Display supported products (condensed for multiple drivers)
            if "series" in driver_info:
                print(f"\nSupported GPU Series:")
                series_names = []
                for series in driver_info["series"]:
                    series_name = urllib.parse.unquote(series.get("seriesname", "Unknown Series"))
                    series_names.append(series_name)
                print(f"{', '.join(series_names[:5])}")
                if len(series_names) > 5:
                    print(f"and {len(series_names) - 5} more...")
            
            # Add separator between drivers (except for the last one)
            if idx < num_drivers:
                print("=" * 60)

    def lookup(self, product_id, os_id, lang_id, series_id):
        dch_1_oses = ["57", "135"]  # Windows 10 64-bit and Windows 11
        dch_value = "1" if str(os_id) in dch_1_oses else "0"
        
        query_url = (
            f"https://gfwsl.geforce.com/services_toolkit/services/com/nvidia/services/AjaxDriverService.php?func=DriverManualLookup"
            f"&pfid={product_id}&osID={os_id}&languageCode={lang_id}&dch={dch_value}&dltype=-1&numberOfResults={RESULTS}&psid={series_id}"
        )

        print(f"\nQuery URL: {query_url}")
        
        try:
            response = requests.get(query_url)
            response.raise_for_status()
            data = response.json()
            self.display_results(data)
        except Exception as e:
            print(f"Failed to fetch driver data: {e}")

    def run(self):
        print("NVIDIA Driver Lookup CLI")
        print("=" * 30)
        
        # Load initial data
        if not self.load_initial_data():
            return
        
        # Select product family
        selected_family = self.get_user_choice(
            self.display_menu(self.product_families, "Product Families"),
            "Select a product family"
        )
        family_id = selected_family["id"]
        
        # Load and select series
        if not self.load_series_data(family_id):
            return
        
        selected_series = self.get_user_choice(
            self.display_menu(self.current_series, "Product Series"),
            "Select a product series"
        )
        series_id = selected_series["id"]
        
        # Load and select product
        if not self.load_products_data(family_id, series_id):
            return
        
        selected_product = self.get_user_choice(
            self.display_menu(self.current_products, "Products"),
            "Select a product"
        )
        product_id = selected_product["id"]
        
        # Select OS
        selected_os = self.get_user_choice(
            self.display_menu(self.os_options, "Operating Systems"),
            "Select an operating system"
        )
        os_id = selected_os["id"]
        
        # Select language
        selected_language = self.get_user_choice(
            self.display_menu(self.language_options, "Languages"),
            "Select a language"
        )
        lang_id = selected_language["id"]
        
        # Perform lookup
        print(f"\nSearching for drivers...")
        print(f"Product: {selected_product['menutext']}")
        print(f"OS: {selected_os['menutext']}")
        print(f"Language: {selected_language['menutext']}")
        
        self.lookup(product_id, os_id, lang_id, series_id)

# Run CLI
if __name__ == "__main__":
    cli = NvidiaDriverLookupCLI()
    cli.run()
