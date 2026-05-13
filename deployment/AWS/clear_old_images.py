import subprocess
import json

# Define the service name
service_name = 'perch-social'

def get_container_images(service_name):
    # Run the AWS CLI command to get container images
    result = subprocess.run(
        ['aws', 'lightsail', 'get-container-images', '--service-name', service_name],
        capture_output=True, text=True
    )

    # Check if the command was successful
    if result.returncode != 0:
        print(f"Error fetching images: {result.stderr}")
        return []

    # Parse the JSON output
    return json.loads(result.stdout)['containerImages']

def delete_container_image(service_name, image_name):
    # Run the AWS CLI command to delete a container image

    result = subprocess.run(
        ['aws', 'lightsail', 'delete-container-image', '--service-name', service_name, '--image', image_name],
        capture_output=True, text=True
    )

    # Check if the command was successful
    if result.returncode != 0:
        print(f"Error deleting image {image_name}: {result.stderr}")
    else:
        print(f"Deleted image: {image_name}")

def main():
    # Get all container images
    images = get_container_images(service_name)


    # Sort images by creation date in descending order
    sorted_images = sorted(images, key=lambda x: x['createdAt'], reverse=True)

    #Leaving the 15 most recent ones
    images_to_delete = sorted_images[25:]

    # Delete each of the selected images
    for image in images_to_delete:
        image_name = image['image']
        delete_container_image(service_name, image_name)

if __name__ == "__main__":
    main()