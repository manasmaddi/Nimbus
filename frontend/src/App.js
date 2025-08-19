import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import {
  FileUp,
  LogIn,
  LogOut,
  CheckCircle,
  XCircle,
  Loader2,
  CloudUpload,
} from 'lucide-react';
import axios from 'axios';

const App = () => {
  const { isAuthenticated, loginWithRedirect, logout, getAccessTokenSilently } =
    useAuth0();
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleLogin = () => {
    loginWithRedirect();
  };

  const handleLogout = () => {
    logout({ returnTo: window.location.origin });
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadStatus('');
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadStatus('No file selected.');
      return;
    }

    if (!isAuthenticated) {
      setUploadStatus('You must be logged in to upload a file.');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading...');

    try {
      // Get the access token to send to the backend
      const accessToken = await getAccessTokenSilently({
        audience: process.env.REACT_APP_AUTH0_API_IDENTIFIER,
      });

      const formData = new FormData();
      formData.append('file', file);

      // Make the API call to your Flask backend
      const response = await axios.post(
        `${process.env.REACT_APP_API_BASE_URL}/api/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${accessToken}`, // Send the access token
          },
        }
      );

      setUploadStatus(response.data.message || 'Upload successful!');
    } catch (error) {
      console.error('File upload failed:', error);
      setUploadStatus(
        `Upload failed: ${error.response?.data?.message || error.message}`
      );
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white shadow-xl rounded-2xl p-8 max-w-lg w-full transform transition duration-500 hover:scale-105">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">
          File Upload Portal
        </h1>

        <div className="mb-6 flex justify-center">
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="flex items-center px-6 py-3 bg-red-600 text-white font-semibold rounded-full shadow-lg hover:bg-red-700 transition duration-300"
            >
              <LogOut className="mr-2" size={20} />
              Sign Out
            </button>
          ) : (
            <button
              onClick={handleLogin}
              className="flex items-center px-6 py-3 bg-blue-600 text-white font-semibold rounded-full shadow-lg hover:bg-blue-700 transition duration-300"
            >
              <LogIn className="mr-2" size={20} />
              Sign In with Auth0
            </button>
          )}
        </div>

        {isAuthenticated && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-700 mb-4 text-center">
              Upload a File to S3
            </h2>
            <form onSubmit={handleFileUpload} className="space-y-4">
              <label
                htmlFor="file-input"
                className="block text-sm font-medium text-gray-700"
              >
                Choose a file:
              </label>
              <div className="flex items-center justify-center w-full">
                <label
                  htmlFor="file-input"
                  className="flex flex-col items-center justify-center w-full h-48 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors duration-300"
                >
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <CloudUpload className="w-10 h-10 mb-3 text-gray-400" />
                    <p className="mb-2 text-sm text-gray-500">
                      <span className="font-semibold">Click to upload</span> or
                      drag and drop
                    </p>
                    {file ? (
                      <p className="text-xs text-gray-400 mt-1">
                        Selected: {file.name}
                      </p>
                    ) : (
                      <p className="text-xs text-gray-400 mt-1">
                        Any file type is acceptable
                      </p>
                    )}
                  </div>
                  <input
                    id="file-input"
                    type="file"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </label>
              </div>

              <button
                type="submit"
                disabled={!file || isUploading}
                className="w-full flex items-center justify-center px-6 py-3 bg-green-600 text-white font-semibold rounded-full shadow-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-green-700 transition duration-300"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 animate-spin" size={20} />
                    Uploading...
                  </>
                ) : (
                  <>
                    <FileUp className="mr-2" size={20} />
                    Upload File
                  </>
                )}
              </button>
            </form>

            {uploadStatus && (
              <div
                className={`mt-4 p-4 rounded-lg flex items-center ${
                  uploadStatus.includes('failed') ||
                  uploadStatus.includes('No file selected')
                    ? 'bg-red-100 text-red-700'
                    : 'bg-green-100 text-green-700'
                }`}
              >
                {uploadStatus.includes('successful') ? (
                  <CheckCircle className="mr-3" size={20} />
                ) : (
                  <XCircle className="mr-3" size={20} />
                )}
                {uploadStatus}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
