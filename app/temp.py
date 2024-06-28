@app.put("/submit-slate/{form_id}")
async def update_form(request: Request, form_id: str):
    try:
        form = await request.form()
        json_data = json.loads(form["json"])
        
        files = form.getlist("files")
        
        filename_mapping = {}
        
        for file in files:
            if isinstance(file, UploadFile):
                original_filename = file.filename
                unique_filename = f"{uuid.uuid4()}_{original_filename}"
                filename_mapping[original_filename] = unique_filename
                
                contents = await file.read()
                
                # Upload file to Digital Ocean Spaces
                spaces_client.put_object(
                    Bucket=DO_SPACE_NAME,
                    Key=unique_filename,
                    Body=contents,
                    ACL='public-read'
                )
        
        # Update JSON data with new filenames
        for field_name, field_value in json_data['data'].items():
            if isinstance(field_value, list):
                for item in field_value:
                    for key, value in item.items():
                        if value in filename_mapping:
                            item[key] = f"https://{DO_SPACE_NAME}.{DO_SPACE_REGION}.digitaloceanspaces.com/{filename_mapping[value]}"

        # Update MongoDB
        update_result = await assigned_slates.update_one(
            {"_id": ObjectId(form_id)},
            {"$set": json_data}
        )
        
        if update_result.modified_count == 0:
            return JSONResponse(status_code=404, content={"message": "Form not found or not modified"})
        
        return JSONResponse(content={"message": "Form updated successfully", "data": json_data})
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})