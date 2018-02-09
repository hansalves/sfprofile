# sfprofile

Python script that can be used to quickly set permissions in salesforce profiles.

### Usage

Run the script from the source folder of a package retrieved using the Salesforce Ant Migration Tool or the force.com CLI.

The script expects a folder named profiles to exist in the working directory, and will look for .profile files there. By default the modified profiles will be written to a new file named something like `oldprofile.profile.new'. This can be changed by using the -i parameter.
Unless the -p parameter is given, all profiles in the profiles directory will be processed.

Use the -h parameter for explanation on the other options.

All parameters that accept arguments can be passed more than once.

### Examples

    ./sfprofile.py -a Account -p Admin

Will look for profiles/Admin.profile and create a new file profiles/Admin.profile.new in which all permissions on the Account are set to true *and* the field level security for all Account fields, that are found in the profile, are set to true.

    ./sfprofile.py -a Account -a Contact -i

Will modify all profiles in the profiles directory in place, and set all permissions and field level security settings, that are found in the profile, for the Account and Contact objects to true.

Note that profiles retrieved by the Ant Migration Tool or force.com CLI only contain settings for the objects and fields that are simultaneously retrieved. It is therefore recommended to use profile files that are fetched together with all other metadata in your Salesforce org.

    ./sfprofile.py -f MyCustomObject__c true true true false false false -p MyCustomProfile -i

Will set the object permissions for MyCustomObject__c to read,create,edit without delete, viewall or modifyall permissions in `profiles/MyCustomProfile.profile'. If no permissions for this object are found in a profile they will be added.

    ./sfprofile.py -f Account.MyCustomField__c true false

Will set the field level security for Account.MyCustomField__c to readable but not editable, for all found profiles. If no permissions for this field are found in a profile they will be added.

