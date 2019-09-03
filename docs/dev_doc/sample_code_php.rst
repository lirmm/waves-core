WAVES API php samples code
=========================

Create functions for GET and POST requests
---------------------------------------

.. code-block:: php

    function callApiGET($url_api, $token='', $type='json')
        {
            $authorization = "Authorization: Token ".$token;
            $content_type=($type == "html")?'Content-Type: txt/html':'Content-Type: application/json';
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $url_api);
            curl_setopt($ch, CURLOPT_HTTPHEADER, array('Accept: application/json', $content_type , $authorization));
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
            curl_setopt($ch, CURLOPT_POST, 0);

            $curl_response = curl_exec($ch);
            if ($curl_response === false)
            {
                // throw new Exception('Curl error: ' . curl_error($crl));
                $rep = 'Curl error: ' . curl_error($ch);
                var_dump($rep);
            } else
            {
                // For debug :
                //print_r(curl_getinfo($ch));
                $rep = ($type=="html")?$curl_response:json_decode($curl_response);
            }
            curl_close($ch);
            return $rep;
        }

        // Appel l'API WAVES en requête http POST
    function callApiPOST($url_api, $token='', $data_string)
        {
            $authorization = "Authorization: Token ".$token;
            $content_type='Content-Type: multipart/form-data';
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $url_api);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [$content_type , $authorization]);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data_string);
    
            $curl_response = curl_exec($ch);
            if ($curl_response === false)
            {
                // throw new Exception('Curl error: ' . curl_error($crl));
                $rep = 'Curl error: ' . curl_error($ch);
                var_dump($rep);
            }
            else
            {
                // For debug :
                //print_r(curl_getinfo($ch));
                $rep = json_decode($curl_response);
            }
            curl_close($ch);
            return $rep;
        }


Display the list of services
----------------------------

.. code-block:: php

    $urlwaves = "http://waves.demo.atgc-montpellier.fr/waves";
    $base_api = $urlwaves."/api/";
    $api_key = "6241961ef45e4bbe7bb01a05f938ed9f0f2a3926";

    $url_api = $base_api.'services';

    $tabrep = callApiGET($url_api, $api_key);
    $html = '<p>';
    $html = 'Here is the list of services<br>name : service_app_name <br>';
    foreach ($tabrep as $obj) {
        $html .= $obj->name." : ".$obj->service_app_name."<br>";
    }
    $html .= '</p>';
    echo $html;


Integrate a WAVES service form
------------------------------

.. code-block:: php

    $html='';

    foreach ($tabrep as $obj) {
        if ($obj->service_app_name == 'sample_service') {
            $url_form = $obj->form;
        }
    }

    if($url_api!='') {
        $html .=callApiGET($url_form, $api_key, 'html');
    } else {
        $html = 'pb with url_api';
    }
    echo $html;


Create a job
------------

.. code-block:: php

    $submit_url = $url_api.'/sample_service/submissions/default/jobs';

	$data = [
        "title"=>"Job Name",
        "input_file"=> new CurlFile('test.fasta', 'text/plain')
        ];

	$tabrep = callApiPOST($submit_url, $api_key, $data);
 	
    echo '<div id="reponse"><pre>';
    print_r($tabrep);
    echo '</pre></div>';
	
	$status = $tabrep->status;
	
    if ($status->code==0) {
		$api_html = '<p>You\'re job is submitted. Follow it on <a target="_new" href="'.$tabrep->url.'">'.$tabrep->url."</a>. Warning you have to be logged on admin (due to authentication)</p>";
	} else {
		$api_html = "<p>An error occurred... call your admin ;-)</p>"; 
	}
	echo $api_html;
