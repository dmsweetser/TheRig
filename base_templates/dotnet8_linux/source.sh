#!/bin/bash

echo "Setting up .NET environment..."

# Check if .NET 8 is installed
if ! command -v dotnet &>/dev/null; then
    echo "Error: .NET 8 is not installed. Please install .NET 8 before running this script."
    exit 1
fi

echo ".NET 8 is installed."

# Restore NuGet packages
dotnet restore packages.config
if [ $? -ne 0 ]; then
    echo "Error: Unable to restore NuGet packages."
    exit 1
fi

echo "NuGet packages restored successfully."

# Build the .NET application
dotnet build source.csproj --configuration Release
if [ $? -ne 0 ]; then
    echo "Error: Unable to build the .NET application."
    exit 1
fi

echo ".NET application built successfully."

# Run the .NET application
timeout -s KILL 20 dotnet run --project source.csproj
if [ $? -ne 0 ]; then
    echo "Error: Unable to run the .NET application."
    exit 1
fi

echo ".NET application executed successfully."