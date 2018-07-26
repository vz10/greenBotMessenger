var Client = require('azure-iothub').Client;

module.exports = function (context, req) {
    context.log('JavaScript HTTP trigger function processed a request.');

    if (req.body && req.body.action) {
        // Using the Node.js Service SDK for IoT Hub:
        //   https://github.com/Azure/azure-iot-sdk-node
        // The sample connects to service-side endpoint to call direct methods on devices.

        let host_name = process.env.DEVICE_HOST;
        let shared_access_key_name = process.env.DEVICE_ACCESS_KEY_NAME;
        let shared_access_key = process.env.DEVICE_ACCESS_KEY;

        if(!(host_name && shared_access_key_name && shared_access_key)){
            let error_msg = 'Device access is not configured';
            console.error(error_msg);
            context.res = {
                status: 500,
                body: error_msg
            };
            context.done();
            return 1;
        }

        let deviceId = 'MyPythonDevice';

        // Connect to the service-side endpoint on IoT hub.
        let client = Client.fromConnectionString(
            `HostName=${host_name};SharedAccessKeyName=${shared_access_key_name};SharedAccessKey=${shared_access_key}`);

        // Set the direct method name, payload, and timeout values
        let methodParams = {
            methodName: 'PerformAction',
            payload: req.body.action,
            responseTimeoutInSeconds: 30
        };

        // Call the direct method on your device using the defined parameters.
        client.invokeDeviceMethod(deviceId, methodParams, function (err, result) {
            if (err) {
                let error_msg = 'Failed to invoke method \'' + methodParams.methodName + '\': ' + err.message;
                context.log(error_msg);
                context.res = {
                    status: 500,
                    body: error_msg
                };
            } else {
                context.log('Response from ' + methodParams.methodName + ' on ' + deviceId + ':');
                context.log(JSON.stringify(result, null, 2));
                context.res = {
                    // status: 200, /* Defaults to 200 */
                    body: "Action performed"
                };
            }
            context.done();
        });

    }
    else {
        context.res = {
            status: 400,
            body: "'action' is not provided"
        };
        context.done();
    }
};
