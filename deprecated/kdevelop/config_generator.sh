echo "your user id is: $(id -u)"

XCC_USER_ID=$(id -u)

echo "{" > kdev_config.json
echo -e "\t\"XCC_USER_ID\" : \"$XCC_USER_ID\"" >> kdev_config.json
echo "}" >> kdev_config.json
