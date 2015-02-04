import os.path

private_config_filename = "./thought_lounge/private_config.py"
if not os.path.isfile(private_config_filename):
    import uuid
    myfile = open(private_config_filename, 'w')
    myfile.write("SECRET_KEY = '{0}'\n".format(uuid.uuid4()))
    myfile.close()

from thought_lounge import app
app.run(debug = True)
